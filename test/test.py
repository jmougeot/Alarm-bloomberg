import os, site, sys
site_packages = site.getsitepackages()[0]
qt_path = site_packages + r"\PySide6\plugins\platforms"
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_path

print("sys.executable =", sys.executable)
print("site_packages  =", site_packages)
print("qt_path set    =", qt_path)
print("env now        =", os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"))
print("exists dir     =", os.path.isdir(qt_path))
print("exists dll     =", os.path.isfile(os.path.join(qt_path, "qwindows.dll")))
