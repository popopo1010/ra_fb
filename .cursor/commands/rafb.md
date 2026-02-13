# 初回架電フィードバック（/rafb）

初回架電の文字起こしからフィードバックを生成し、Slack `#dk_ra_初回架電fb` に投稿する。

## あなたの役割

ユーザーが `/rafb` を実行したら、以下を実施する。

### 1. 入力の特定

- ユーザーがファイルパスを指定 → そのパスを使用
- ユーザーが架電記録（`references/long_calls/` 配下の .md）を開いている → そのファイルを使用
- ユーザーが文字起こしを貼り付け → 一時ファイルに保存してから実行
- どれもない場合 → 「文字起こしのファイルパスを教えてください」または「架電記録のファイルを開いた状態で /rafb を実行してください」と返答

### 2. スクリプトの実行

```bash
cd /Users/ikeobook15/RA_FBシステム
python3 scripts/generate_feedback.py <ファイルパス>
```

- `--no-slack` … Slack に送らず標準出力のみ（テスト時）
- `--no-ai` … AI を使わずテンプレートのみ

### 3. 結果の報告

- 成功時：「#dk_ra_初回架電fb に投稿しました」と表示
- 失敗時：エラー内容を確認し、.env の SLACK_WEBHOOK_URL などを案内

## リファレンス

- `references/manual/営業新規架電マニュアル.md`
- `references/manual/PSS_プロフェッショナルセリングスキル.md`（PSS: オープニング・プロービング・サポーティング・クロージング）
- `references/初回面談_確認チェックリスト.md`
- `references/long_calls/受付突破_断りパターンと繋ぎ方.md`
- `references/long_calls/茂野vs小山田_課題整理.md`
