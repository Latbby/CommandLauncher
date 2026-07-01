# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/command_launcher/main.py'],
    pathex=[],
    binaries=[],
    # 将图标复制进打包目录，供 Qt 运行时窗口图标读取。
    datas=[('assets/icon.ico', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Python SSL — 应用不发起 HTTPS 请求，排除以节省 libcrypto/libssl (~4 MB)
        'ssl',
        '_ssl',
        # 排除未使用的 PySide6 子模块，减少连带打包的 Python 层代码
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.QtPdf',
        'PySide6.QtVirtualKeyboard',
        'PySide6.QtDesigner',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtSerialPort',
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtSensors',
        'PySide6.QtSpatialAudio',
        'PySide6.QtTextToSpeech',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DLogic',
        'PySide6.QtQuick3D',
        'PySide6.QtDataVisualization',
        'PySide6.QtGraphs',
        'PySide6.QtGraphsWidgets',
        'PySide6.QtHttpServer',
        'PySide6.QtPositioning',
        'PySide6.QtRemoteObjects',
        'PySide6.QtSql',
        'PySide6.QtCharts',
    ],
    noarchive=False,
    optimize=0,
)

# ——— 清理多余二进制文件 ————————————————————————————————————————————
# PyInstaller 会连带打包很多项目根本用不到的 Qt DLL。
# 在 Analysis 之后、EXE 打包之前，从 TOC 列表中移除它们。

# 不需要的 DLL 文件名模式（不区分大小写）
_unwanted_dlls = {
    # 软件 OpenGL 渲染器（7+ MB 压缩后）— 现代 Windows 都支持硬件 OpenGL
    'opengl32sw.dll',
    # Qt Quick / QML（~6 MB 压缩后）— 项目使用 Qt Widgets，无需这些
    'qt6quick.dll',
    'qt6qml.dll',
    'qt6qmlmodels.dll',
    'qt6quickcontrols2.dll',
    'qt6quickcontrols2impl.dll',
    'qt6quicktemplates2.dll',
    'qt6quickshapes.dll',
    'qt6quicklayouts.dll',
    'qt6quickdialogs2.dll',
    'qt6quickdialogs2quickimpl.dll',
    'qt6quickwidgets.dll',
    'qt6labsanimation.dll',
    'qt6labssharedimage.dll',
    'qt6labswavefrontmesh.dll',
    'qt6labsqmlmodels.dll',
    'qt6labsfolderlistmodel.dll',
    'qt6labssettings.dll',
    # PDF（2.3 MB 压缩后）
    'qt6pdf.dll',
    'qt6pdfwidgets.dll',
    'qt6pdfquick.dll',
    # 虚拟键盘（0.2 MB）
    'qt6virtualkeyboard.dll',
    # Qt Designer（5 MB 压缩前）
    'qt6designer.dll',
    # Web 相关
    'qt6webchannel.dll',
    'qt6webenginecore.dll',
    'qt6webengine.dll',
    'qt6webenginewidgets.dll',
    'qt6webenginequick.dll',
    # 多媒体
    'qt6multimedia.dll',
    'qt6multimediawidgets.dll',
    'qt6multimediaquick.dll',
    # 3D
    'qt63dcore.dll',
    'qt63dinput.dll',
    'qt63drender.dll',
    'qt63danimation.dll',
    'qt63dextras.dll',
    'qt63dlogic.dll',
    'qt6quick3d.dll',
    'qt6quick3druntimerender.dll',
    'qt6quick3dassetimport.dll',
    'qt6quick3dassetutils.dll',
    'qt6quick3deffects.dll',
    'qt6quick3dhelpers.dll',
    'qt6quick3diblbaker.dll',
    'qt6quick3dparticles.dll',
    'qt6quick3dutils.dll',
    # 其他
    'qt6shadertools.dll',
    'qt6bluetooth.dll',
    'qt6nfc.dll',
    'qt6sensors.dll',
    'qt6serialport.dll',
    'qt6serialbus.dll',
    'qt6spatialaudio.dll',
    'qt6texttospeech.dll',
    'qt6positioning.dll',
    'qt6remoteobjects.dll',
    'qt6sql.dll',
    'qt6charts.dll',
    'qt6datavisualization.dll',
    'qt6graphs.dll',
    'qt6graphswidgets.dll',
    'qt6httpserver.dll',
    # Direct2D 平台插件 — Windows 默认使用 qwindows.dll 即可
    'qdirect2d.dll',
    # 不必要的图片格式插件（保留 qico, qsvg 即可满足基本需求）
    'qjpeg.dll',
    # 'qwebp.dll',   # 如果需要 WebP 支持则保留
    'qtiff.dll',
    'qicns.dll',
    'qwbmp.dll',
    # 不相关的 FFmpeg 多媒体编解码器
    'avcodec-61.dll',
    'avformat-61.dll',
    'avutil-59.dll',
    'swresample-5.dll',
    'swscale-8.dll',
    # 多余的平台插件 — Windows 只需要 qwindows.dll
    'qoffscreen.dll',
    'qminimal.dll',
    # OpenSSL TLS 后端 — Windows 使用 Schannel (qschannelbackend.dll)
    'qopensslbackend.dll',
    'qcertonlybackend.dll',
    # 不需要的通用插件
    'qtuiotouchplugin.dll',
    'qnetworklistmanager.dll',
    'qtvirtualkeyboardplugin.dll',
    # QML 残余 — 项目不涉及 QML
    'qt6qmlmeta.dll',
    'qt6qmlworkerscript.dll',
    # 不需要的图片格式插件
    'qpdf.dll',     # PDF 作为图片格式
    'qtga.dll',     # Truevision TGA 格式
    'qgif.dll',     # GIF 格式（如不需要可保留此行）
    # OpenSSL — 保留 Python hashlib 纯 Python 回退，移除底层 DLL (~4 MB)
    # Windows 上 Qt 使用 Schannel 做 TLS，不需要 OpenSSL
    'libcrypto-3.dll',
    'libcrypto-3-x64.dll',
    'libssl-3-x64.dll',
    '_hashlib.pyd',  # 无 OpenSSL 则此扩展无法加载，hashlib 自动回退
}

def _keep_binary(toc_entry):
    """判断一个 (name, path, typecode) 是否应该保留。"""
    import os
    # toc_entry[0] 格式如 "PySide6\\Qt6Quick.dll"，提取纯文件名比较
    basename = os.path.basename(toc_entry[0].lower())
    # 如果文件名在排除列表中，则丢弃
    if basename in _unwanted_dlls:
        return False
    return True

a.binaries = [b for b in a.binaries if _keep_binary(b)]

# ——— 清理多余翻译文件 —————————————————————————————————————————————————
# 只保留中文翻译，移除其他 40+ 种语言以节省约 1.5 MB
a.datas = [
    d for d in a.datas
    if not (
        d[0].lower().endswith('.qm')
        and 'zh_cn' not in d[0].lower()
    )
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name='命令启动器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 将图标写入 exe 的 PE 资源，供 Windows 资源管理器读取。
    icon=['assets/icon.ico'],
)
