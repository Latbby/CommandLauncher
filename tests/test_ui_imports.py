def test_ui_modules_import():
    from command_launcher.app import create_app
    from command_launcher.ui.main_window import MainWindow

    assert create_app is not None
    assert MainWindow is not None
