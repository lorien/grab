"""
This module just displays captcha image in the browser and
then read captcha solution from the console input.
"""
import tempfile
import webbrowser
import time
import os

#def build_html(image_url):
    #return """
        #<img src="%s" />
        #<script type="text/javascript">
            #setTimeout(5000, window.close);
        #</script>
    #""" % image_url

    
def solve_captcha(data, *args, **kwargs):
    fd, image_path = tempfile.mkstemp()
    open(image_path, 'w').write(data)
    image_url = 'file://' + image_path
    #page_path = tempfile.mkstemp()
    #html = build_html(image_url)
    #open(page_path, 'w').write(html)
    #page_url = 'file://' + page_path

    webbrowser.open(url=image_url)
    # Sleep for short to display rrors which
    # browser could display to stdout
    time.sleep(0.2)
    solution = raw_input('Solution: ')
    os.unlink(image_path)
    return solution
