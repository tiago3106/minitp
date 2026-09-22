$ErrorActionPreference = "Stop"
$proc = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -PassThru -WindowStyle Hidden
try {
    Start-Sleep -Seconds 4
    $listo = $false
    for ($i = 0; $i -lt 30 -and -not $listo; $i++) {
        try { Invoke-RestMethod "http://127.0.0.1:8000/productos?limit=1" | Out-Null; $listo = $true } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $listo) { throw "El servidor no arrancó a tiempo." }

    $header = & curl.exe -s -D - -o NUL "http://127.0.0.1:8000/productos?limit=2" | Select-String -Pattern "X-Total"
    Write-Output ("GET /productos (paginado)   -> header: " + $header)

    $uno = Invoke-RestMethod "http://127.0.0.1:8000/productos/1"
    Write-Output ("GET /productos/1             -> nombre=" + $uno.nombre + " | precio=" + $uno.precio + " (tipo " + $uno.precio.GetType().Name + ")")

    $creado = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/productos" -ContentType "application/json" -Body '{"nombre":"Test","precio":"99.90","stock":5,"stock_reservado":1,"habilitado":true}'
    Write-Output ("POST /productos              -> id=" + $creado.id + " | stock=" + $creado.stock)

    $nulo = Invoke-RestMethod -Method Patch "http://127.0.0.1:8000/productos/$($creado.id)" -ContentType "application/json" -Body '{"categoria":null,"nombre":"Test 2"}'
    if ($null -eq $nulo.categoria) { $catMsg = "null (R10 OK)" } else { $catMsg = "NO aplico el null (R10 falla)" }
    Write-Output ("PATCH categoria=null (R10)   -> nombre=" + $nulo.nombre + " | categoria: " + $catMsg)

    $omitido = Invoke-RestMethod -Method Patch "http://127.0.0.1:8000/productos/$($creado.id)" -ContentType "application/json" -Body '{"precio":"80.00"}'
    Write-Output ("PATCH sin enviar nombre (R10) -> nombre sigue=" + $omitido.nombre + " | precio=" + $omitido.precio)

    $compado = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/productos/$($creado.id)/comprar" -ContentType "application/json" -Body '{"cantidad":1}'
    Write-Output ("POST /comprar                -> stock restante=" + $compado.stock)

    try { Invoke-RestMethod "http://127.0.0.1:8000/productos/999" | Out-Null } catch { Write-Output ("GET 404 normal                   -> " + ($_.ErrorDetails.Message).Trim()) }
    try { Invoke-RestMethod -Method Post "http://127.0.0.1:8000/productos/4/comprar" -ContentType "application/json" -Body '{"cantidad":1}' | Out-Null } catch { Write-Output ("comprar no habilitado (R9)        -> " + ($_.ErrorDetails.Message).Trim()) }
    try { Invoke-RestMethod -Method Post "http://127.0.0.1:8000/productos/1/comprar" -ContentType "application/json" -Body '{"cantidad":999}' | Out-Null } catch { Write-Output ("sin stock (R9)                    -> " + ($_.ErrorDetails.Message).Trim()) }
    try { Invoke-RestMethod -Method Post "http://127.0.0.1:8000/productos" -ContentType "application/json" -Body '{"nombre":"x","precio":"10.00","stock":3,"stock_reservado":5}' | Out-Null } catch { Write-Output ("model_validator (R7)              -> 422: " + ($_.Exception.Message -replace "`n"," ")) }

    $seq = Invoke-RestMethod "http://127.0.0.1:8000/comparacion/sincrono"
    $par = Invoke-RestMethod "http://127.0.0.1:8000/comparacion/asincrono"
    Write-Output ("comparacion sincrono (R14)      -> " + $seq.duracion_ms + " ms")
    Write-Output ("comparacion asincrono (R14)     -> " + $par.duracion_ms + " ms")
}
finally {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}