from grab import Grab

start_page = 'http://www.mplants.org.ua/view_main_right.php?id=3'
grabber = Grab()

grabber.go(start_page)
grabber.response.body = grabber.response.body.replace('cp-1251',
'cp1251')

path_title = '/html/head/title'
buf_title = grabber.xpath_text(path_title)

print buf_title
