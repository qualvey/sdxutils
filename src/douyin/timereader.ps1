# 假设 JSON 文件路径
$jsonPath = "./douyin-review.json"
$jsonContent = Get-Content $jsonPath -Raw | ConvertFrom-Json

function Convert-PublicedTime($obj) {
    if ($obj -is [PSCustomObject]) {
        foreach ($prop in $obj.PSObject.Properties) {
            if ($prop.Name -eq "publiced_time") {
                $timestamp = [int64]$prop.Value
                $dt = (Get-Date "1970-01-01 00:00:00").AddSeconds($timestamp).AddHours(8)
                $obj.$($prop.Name) = $dt.ToString("yyyy-MM-dd HH:mm:ss")
                Write-Host "Converted publiced_time: $($obj.$($prop.Name))"
            } else {
                Convert-PublicedTime $prop.Value
            }
        }
    }
    elseif ($obj -is [System.Collections.IEnumerable] -and -not ($obj -is [string])) {
        foreach ($item in $obj) {
            Convert-PublicedTime $item
        }
    }
}

# 执行转换
Convert-PublicedTime $jsonContent

# 保存回文件
$jsonContent | ConvertTo-Json -Depth 100 | Set-Content "data_cst.json"
