openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 -subj '/O=example Inc./CN=example.com' -keyout example.com.key -out example.com.crt
openssl req -out mcp.example.com.csr -newkey rsa:2048 -nodes -keyout mcp.example.com.key -subj "/CN=mcp.example.com/O=mcp organization"
openssl x509 -req -sha256 -days 365 -CA example.com.crt -CAkey example.com.key -set_serial 0 -in mcp.example.com.csr -out mcp.example.com.crt
