# Naive Scrcpy Client

A naive client of [Scrcpy](https://github.com/Genymobile/scrcpy) in Python. 
Currently it can only decode video stream from the server. 

This client was inspired by [py-scrcpy](https://github.com/Allong12/py-scrcpy).

### Dependence
* Android Debug Bridge
* ffmpeg shared libraries
* opencv-pythons (for GUI)

### To Start
1. Install OpenCV for Python. Naive Scrcpy Client use OpenCV for GUI. 
You can replace it with PIL or anything else easily.
   ```
   pip install opencv-python
   ```
2. Copy/link recent ffmpeg __shared__ libraries to [/lib](/lib), the required files were listed below. 
Make sure the version of libs match to the architecture of your Python (e.g. x86->32bit). 
   * Windows:
   ```
   avcodec-58.dll
   avformat-58.dll
   avutil-56.dll
   swresample-3.dll
   ```
   * Linux:
   ```
   libavcodec.so
   libavformat.so
   libavutil.so
   libswresample.so
   ```
3. Get ADB ready on your PC and leave USB Debug Mode open on your phone.

4. Let's rock!
   ```
   python run_client.py
   ```
5. Check config in [run_client.py](run_client.py) for more information.

### Contact me
* (Recommended) New issue 
* Email: lostxine@gmail.com
