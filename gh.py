from ghost import Ghost

ghost = Ghost()
page, extra_resources = ghost.open('http://yandex.ru/robots.txt')
print page
#assert page.http_status==200 and 'jeanphix' in ghost.content
