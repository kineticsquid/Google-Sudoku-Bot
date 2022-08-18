# Google DialogFlow Sudoku Bot

### Twilio API
- https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python

### Install
python3 -m pip install dialogflow 

### List available packages
```
import pkg_resources
installed_packages = pkg_resources.working_set
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
   for i in installed_packages])

for item in installed_packages_list:
    print(item)
```
### Evaluating Image Processing
- **`test_hough_lines` notebook** - for an individual image tests finding hough lines and then refining them into boundaries for the 81 cells that make up the Sudoku matrix. Do this first.
- **`test_image_ocr` notebook** - tests the full hough lines, cell boundaries and OCR for a single image. Do this second.
- **`test_all_images_ocr notebook** - same as previous, but does this for all images in `test-images`.
- **`test_tesseract_parms` notebook** - tests all known tesseract parameter combinations that could work for an installation. Use this to determine best parameters to process images. Test results in `tesseract scores.xlsx`.







