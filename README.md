# **Unofficial** "Nullsoft Scriptable Install System" (NSIS) fork

Original project's website: https://nsis.sourceforge.io  
Original project's GitHub page: https://github.com/NSIS-Dev/nsis  

[![License: zlib/libpng](https://img.shields.io/badge/License-zlib%2Flibpng-blue.svg)](http://nsis.sourceforge.net/License)
[![Latest Release](https://img.shields.io/badge/dynamic/json.svg?label=Latest%20Release&url=https%3A%2F%2Fapi.github.com%2Frepos%2Fnegrutiu%2Fnsis%2Freleases%2Flatest&query=%24.name&colorB=orange)](../../releases/latest)
[![Downloads](https://img.shields.io/github/downloads/negrutiu/nsis/total.svg?label=Downloads&colorB=orange)](../../releases/latest)
[![Static Badge](https://img.shields.io/badge/GitHub%20Marketplace-negrutiu%2Fnsis--install-blue?style=flat-square&logo=github)
](https://github.com/marketplace/actions/install-nsis-compiler)

This project was started mainly to provide early access to the NSIS 64-bit features.  
It also comes with a few extra plugins and features that you might find useful.

### Features:
- Native `x86` and `amd64` NSIS compilers
- Can produce native `x86` and `amd64` installers, compatible with all Windows versions (NT4+)
- Extra built-in plugins:
  * [NScurl](https://github.com/negrutiu/nsis-nscurl) - Plugin with advanced HTTP/S capabilities. Useful for file transfers, REST API calls, etc.
  * [NSxfer](https://github.com/negrutiu/nsis-nsxfer) - Plugin with advanced HTTP/S capabilities (superseded by NScurl)
  * [NSutils](https://github.com/negrutiu/nsis-nsutils) - Plugin with multiple goodies packed in one basket
  * [ExecDos](https://github.com/negrutiu/nsis-execdos) - Extended support for running child processes
  * [TaskbarProgress](https://github.com/negrutiu/nsis-taskbarprogress) - Display installation progress in Windows taskbar
  * [ShellLink](https://github.com/negrutiu/nsis-shelllink) - Complex operations with shortcut files (`*.lnk`)
- Two new extra-large UI themes [ModernXL](https://github.com/negrutiu/nsis/wiki/ModernXL/) and [ModernXXL](https://github.com/negrutiu/nsis/wiki/ModernXL/)
- Advanced logging enabled (`NSIS_CONFIG_LOG`)
- Larger strings (`NSIS_MAX_STRLEN=4096`)

> [!TIP]
> - A [GitHub Action](https://github.com/marketplace/actions/install-nsis-compiler) is available to install/upgrade __NSIS compiler__ on Windows runners
> - A [GitHub Action](https://github.com/marketplace/actions/install-nsis-plugin) is available to install/upgrade __NSIS plugins__ on Windows, Linux or macOS runners
