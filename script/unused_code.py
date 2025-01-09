

def safe_try(fn, *args,
             error_sig: PySide6.QtCore.Signal = None,
             res_sig: PySide6.QtCore.Signal = None,
             finished_sig: PySide6.QtCore.Signal = None,
             **kwargs):
    try:
        fn(*args, **kwargs)
    except:
        traceback.print_exc()
        exctype, value = sys.exc_info()[:2]
        error_sig.emit((exctype, value, traceback.format_exc()))
    else:
        res_sig.emit("Done.")  # Return the result of the processing
    finally:
        print("FFFFFFFFFFFFFFinish!")
        finished_sig.emit()  # Done