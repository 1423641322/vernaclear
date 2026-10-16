# Vernaclear · 语境译

看懂聊天里的每一种说法。

Vernaclear 是面向真实聊天场景的 Windows 桌面翻译器。首个版本提供文本翻译、图片导入、框选截图 OCR、聊天缩写解释、传统翻译、大模型翻译和自动混合路由。

## 当前功能

- 文本输入、粘贴和结果复制
- 框选当前显示器区域或导入图片进行 OCR
- 内置中、英、日、韩常用聊天缩写与网络表达词库
- 词库 + Microsoft Translator / DeepL 传统翻译
- 任意 OpenAI-compatible 大模型接口，包括本地 Ollama
- 根据缩写歧义自动选择传统翻译或大模型
- 本地历史记录、个人词条和便携数据目录
- Windows DPAPI 加密保存 API 密钥

## 开发运行

推荐 Python 3.12：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe run.py
```

运行测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## 生成便携版

在 PowerShell 中执行：

```powershell
.\build-portable.ps1
```

脚本将在项目上级目录生成 `vernaclear-portable`。其中的 `Vernaclear.exe` 不依赖目标电脑安装 Python。首次 OCR 会加载随程序打包的本地模型，可能需要数秒。

## 翻译服务

应用默认可以进行词库识别与缩写展开，但完整跨语言翻译需要配置至少一种服务：

- Microsoft Translator：填写密钥，可选区域与自定义端点。
- DeepL：填写 API 密钥，可使用 Free 或 Pro 端点。
- OpenAI-compatible：填写 Base URL、模型和密钥；本地 Ollama 默认地址为 `http://localhost:11434/v1`，本地服务可以不填密钥。

API 密钥使用当前 Windows 用户的 DPAPI 加密。复制便携目录到另一台电脑后，需要重新填写密钥。

## 隐私

- OCR 完全在本机执行。
- 截图默认不保存。
- 翻译历史保存在程序目录的 SQLite 数据库中。
- 只有用户主动翻译时，文本才会发送给所选翻译服务。

