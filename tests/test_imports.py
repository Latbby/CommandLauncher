def test_package_imports():
    import command_launcher

    assert command_launcher.__version__ == "0.1.0"
