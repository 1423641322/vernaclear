Vernaclear · 语境译 0.1.0
==============================

双击 Vernaclear.exe 运行，无需安装 Python。

首次使用：
1. 打开“设置”。
2. 配置 Microsoft Translator、DeepL 或 OpenAI-compatible 大模型接口。
3. 也可以保持未配置状态，先体验内置聊天缩写识别与展开。

本地数据：
- config：设置与加密后的 API 密钥
- data：个人词库、历史记录和临时截图
- logs：预留日志目录

API 密钥由 Windows DPAPI 加密。把此文件夹复制到其他电脑或其他 Windows
账户后，请重新填写密钥。

OCR 在本机执行。只有主动翻译时，识别出的文字才会发送给所选翻译服务。

