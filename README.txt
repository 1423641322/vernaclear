Vernaclear · Context Translator 0.2.0
=====================================

中文使用说明
------------

双击 Vernaclear.exe 运行，无需安装 Python。

首次使用：
1. 点击右上角“EN”可切换到英文界面，再次点击“中文”可切回中文。
2. 打开“设置”。
3. 配置 Microsoft Translator、DeepL 或 OpenAI-compatible 大模型接口。
4. 也可以保持未配置状态，先体验内置聊天缩写识别与展开。

主要操作：
- 在左侧输入或粘贴聊天内容，然后点击“开始翻译”。
- 点击“导入图片”识别已有图片中的文字。
- 点击“框选截图”或按 Ctrl+Shift+A，框选屏幕区域进行 OCR。
- Ctrl+Enter 可快速开始翻译。

本地数据：
- config：设置与加密后的 API 密钥
- data：个人词库、历史记录和临时截图
- logs：诊断日志

API 密钥由 Windows DPAPI 加密。把此文件夹复制到其他电脑或其他 Windows
账户后，请重新填写密钥。

OCR 在本机执行。只有主动翻译时，识别出的文字才会发送给所选翻译服务。

许可证：Vernaclear 使用 GNU General Public License v3.0。第三方组件仍适用
各自许可证，详见 LICENSE 和 THIRD_PARTY_NOTICES.md。


English Instructions
--------------------

Double-click Vernaclear.exe to start. Python does not need to be installed.

First use:
1. Click “EN” in the upper-right corner to switch to English. Click “中文” to
   switch back to Chinese.
2. Open “Settings”.
3. Configure Microsoft Translator, DeepL, or an OpenAI-compatible LLM service.
4. You can also leave the services unconfigured and use the built-in chat
   abbreviation recognition and expansion features.

Main actions:
- Enter or paste a chat message on the left, then click “Translate”.
- Click “Import Image” to recognize text in an existing image.
- Click “Capture Area” or press Ctrl+Shift+A to select a screen region for OCR.
- Press Ctrl+Enter to translate quickly.

Local data:
- config: settings and encrypted API keys
- data: personal glossary, translation history, and temporary screenshots
- logs: diagnostic logs

API keys are encrypted with Windows DPAPI. If this folder is copied to another
computer or Windows account, enter the keys again.

OCR runs locally. Recognized text is sent to the selected translation service
only when you explicitly start a translation.

License: Vernaclear is released under the GNU General Public License v3.0.
Third-party components remain subject to their own licenses; see LICENSE and
THIRD_PARTY_NOTICES.md.
