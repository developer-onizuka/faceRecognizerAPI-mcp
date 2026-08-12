# MCP Serverを自作してKubernetesで動かす

# 0. 必要なもの
メモリ24GB程度のノートPC 1台<br>

# 1. Goal
リモートサーバーとしてSSE方式で自作のMCPサーバーを公開し、Claude Desktop等のLLMクライアントへツールを提供すること。

#### Stdio方式と比較したSSE方式のメリット（エンタープライズ性の向上）
- MCPサーバーの一元管理<br>
Stdio方式ではクライアント端末ごとにプログラムの配置や依存関係のアップデートが必要になるが、SSE方式であればサーバー側を更新するだけで、すべてのクライアントに最新のMCPサーバーの機能や改修を即座に反映。

- 実行環境の完全な分離とスケーラビリティ<br>
クライアント側のマシンリソースを消費せず、サーバー側の高スペックなGPUやCPUリソースを活用した重い処理が可能。

```
+-----------------------+              +-------------------------+
|   Claude Desktop      |              |      Kubernetes         |
|                       |              |                         |
|  +-----------------+  |  mcp-remote  |  +-------------------+  |
|  | MCP Client      |--+------------->|--| svc-mcp           |  |
|  +-----------------+  |    (SSE)     |  | (LoadBalancer IP) |  |
|                       |              |  +---------+---------+  |
|                       |              |            |            |
|                       |              |  +---------v---------+  |
|                       |              |  | Pod: mcp-server   |  |
|                       |              |  | (app-mcp.py)      |  |
|                       |              |  +---------+---------+  |
|                       |              |            |            |
|                       |              |  +---------v---------+  |
|                       |              |  | faceRecognizerAPI |  |
|                       |              |  +-------------------+  |
+-----------------------+              +-------------------------+
```

# 2. 各ノードのスペック
| Node名 | CPU | Memory | IP Address |
|---|---|---|---|
| master | 4 | 8GB | 192.168.33.100 |
| worker1 | 4 | 8GB | 192.168.33.101 |

# 3. 手順
### 3-1. Hypervisorのインストール
>https://www.oracle.com/jp/virtualization/technologies/vm/downloads/virtualbox-downloads.html

### 3-2. Vagrantのインストール
>https://developer.hashicorp.com/vagrant/install

### 3-3. gitのインストール & git clone
>https://git-scm.com/downloads
```
git clone https://github.com/developer-onizuka/faceRecognizerAPI-mcp
cd faceRecognizerAPI-mcp
```

### 3-4. Master node / Worker nodeを起動する
```
cd kubernetes
vagrant up
cd ..
```

### 3-5. Master nodeへのログイン & git clone
```
cd kubernetes
vagrant ssh master
git clone https://github.com/developer-onizuka/faceRecognizerAPI-mcp
cd faceRecognizerAPI-mcp
```

### 3-6. Kubernetesクラスタの確認
```
kubectl get nodes -A -o wide
kubectl get pods -A -o wide
```
```
$ kubectl get nodes -A -o wide
NAME      STATUS   ROLES           AGE   VERSION   INTERNAL-IP      EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION     CONTAINER-RUNTIME
master    Ready    control-plane   67m   v1.33.3   192.168.33.100   <none>        Ubuntu 24.04.2 LTS   6.8.0-53-generic   containerd://1.7.27
worker1   Ready    node            67m   v1.33.3   192.168.33.101   <none>        Ubuntu 24.04.2 LTS   6.8.0-53-generic   containerd://1.7.27
```
```
$ kubectl get pods -A -o wide
NAMESPACE        NAME                                       READY   STATUS    RESTARTS   AGE   IP               NODE      NOMINATED NODE   READINESS GATES
kube-system      calico-kube-controllers-7498b9bb4c-lngsr   1/1     Running   0          67m   10.10.219.66     master    <none>           <none>
kube-system      calico-node-4wbbs                          1/1     Running   0          67m   192.168.33.101   worker1   <none>           <none>
kube-system      calico-node-8bt9k                          1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
kube-system      coredns-674b8bbfcf-5strr                   1/1     Running   0          67m   10.10.219.67     master    <none>           <none>
kube-system      coredns-674b8bbfcf-kqn54                   1/1     Running   0          67m   10.10.219.65     master    <none>           <none>
kube-system      csi-nfs-controller-8fdc6755d-78qxc         5/5     Running   0          46m   192.168.33.101   worker1   <none>           <none>
kube-system      csi-nfs-node-kjqnr                         3/3     Running   0          46m   192.168.33.100   master    <none>           <none>
kube-system      csi-nfs-node-x2g8q                         3/3     Running   0          46m   192.168.33.101   worker1   <none>           <none>
kube-system      etcd-master                                1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
kube-system      kube-apiserver-master                      1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
kube-system      kube-controller-manager-master             1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
kube-system      kube-proxy-2xdcj                           1/1     Running   0          67m   192.168.33.101   worker1   <none>           <none>
kube-system      kube-proxy-slq7w                           1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
kube-system      kube-scheduler-master                      1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
metallb-system   controller-58fdf44d87-66bfg                1/1     Running   0          67m   10.10.235.129    worker1   <none>           <none>
metallb-system   speaker-ldcz4                              1/1     Running   0          67m   192.168.33.100   master    <none>           <none>
metallb-system   speaker-v8vn6                              1/1     Running   0          67m   192.168.33.101   worker1   <none>           <none>
```
### 3-7. ロードバランサーの設定
ロードバランサーに割り当てるIPアドレスの範囲を指定します。
```
kubectl apply -f metallb-ipaddress.yaml
```

### 3-8. MCP Serverを動かすPodを起動する
```
kubectl apply -f mcp.yaml
```

### 3-9. Login
```
kubectl exec -it pods/mcp-xxxxxxxxxx-xxxxx -- /bin/bash
```

### 3-10. MCP Serverを起動する
```
git clone https://github.com/developer-onizuka/faceRecognizerAPI-mcp
cd faceRecognizerAPI-mcp
./install-mcp-module.sh
python3 app-mcp.py
```

### 3-11. faceRecognizerAPIを起動する
別ターミナルを開き、Podにログインする。
```
git clone https://github.com/developer-onizuka/faceRecognizerAPI
cd faceRecognizerAPI/
python3 faceRecognizerAPI.py 
```

### 3-12. Inspectorによるテスト
PC側（Claude Desktopを実行するクライアント側）でターミナルを開き、以下を実行する。この際、Node.jsをインストールしておく必要がある。
```
npx @modelcontextprotocol/inspector http://192.168.33.3:5001/sse
```
なおIPアドレスは以下で確認したものを用いる。
```
$ kubectl get services
NAME         TYPE           CLUSTER-IP    EXTERNAL-IP    PORT(S)          AGE
kubernetes   ClusterIP      10.96.0.1     <none>         443/TCP          6h15m
svc-mcp      LoadBalancer   10.97.226.6   192.168.33.3   5001:31904/TCP   6h
```
すると以下のようにブラウザが立ち上がり、MCPの機能をデバックできるようになる。<br>
<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/inspector0.png" width="720"><br><br>
<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/inspector1.png" width="720"><br><br>
<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/inspector2.png" width="720"><br><br>
<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/inspector3.png" width="720"><br><br>
<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/inspector4.png" width="720"><br>

### 3-13. Claude Desktopの起動
claude_desktop_config.jsonに以下を記述した後、Claude Desktopを起動。コネクタとしてface-recognizerが登録されているかを確認する。
```
  "mcpServers": {
    "face-recognizer": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://192.168.33.2:5001/sse",
        "--allow-http"
      ]
    }
  },
```

<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/claudeDesktop-Connector.png" width="720"><br>

### 3-14. プロンプトの入力
```
顔の位置を特定してください。ファイルパスは/faceRecognizerAPI-mcp/Bill.jpgです。
```
なお、このBill.jpgというファイルは手順3-10で、faceRecognizerAPI-mcpをCloneした際に当該ディレクトリ内に保存されているものを使っている。必要に応じて以下コマンドでファイルをPodにコピー可能。
```
kubectl cp new.jpg -n default mcp-xxxxxxxxxx-xxxxx:/faceRecognizerAPI-mcp/new.jpg
```
プロンプト入力後、当該MCPサーバーの許可が求められ、以下のように顔の座標が表示されれば成功となる。

<img src="https://github.com/developer-onizuka/faceRecognizerAPI-mcp/blob/main/claudeDesktop-MCP.png" width="720"><br>

# 4. まとめ
#### MCPクライアント・サーバー間のバイナリ非対応
Claude DesktopなどのMCPクライアントとMCPサーバーの間では、現時点でバイナリファイルの直接的な送受信がプロトコルとして規定されていない。当初はプロンプトにイメージファイルを直接添付してMCPサーバーとの連動を試みたが失敗した。次に、MCP通信がJSONベースで行われる仕様を踏まえ、画像をBase64形式にエンコードしてASCII文字列としてやり取りを試みたが、これもうまくいかなかった。ASCII文字列が長すぎるためと考えられる。<br>
結果として、イメージファイルそのものを送受信するのではなく、MCPサーバーでアクセス可能なファイルパスをテキストで伝達するような手続きをMCPサーバーのPythonスクリプトに記述している。なお、以下がそのJSONベースのやりとりとなる。

- リクエスト（ツール呼び出し）
```
{
  "tool": "face-recognizer:detect_faces",
  "parameters": {
    "image_path": "/faceRecognizerAPI-mcp/Bill.jpg"
  }
}
```
- レスポンス（ツール結果）
```
{
  "facePositions": [
    [
      270,
      444,
      563,
      150
    ]
  ]
}
```

#### エッジ環境の将来性
適切なMCPサーバーを導入することにより、エッジデバイス等の非力な実行環境や軽量な小規模LLMであっても、モデル自体の巨大化や再学習に多大なコストやリソースを投じることなく、高度な外部処理をオフロードして目的を完遂させることが可能となる。
LLM自身にあらゆる処理を抱え込ませるのではなく、何を実行すべきかの判断をLLMに担わせ、画像認識や専門的な計算といった処理を外部のMCPサーバーに切り離すアプローチは、極めて合理的かつ実用的なシステム設計である。この手法により、開発・運用のコストを大幅に抑制しながら、ハルシネーションのリスクを軽減し、リソースの限られた環境やローカル環境においても高度なAIエージェントを堅牢に稼働させることができる。

