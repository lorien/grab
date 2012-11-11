from grab.spider import Spider, Task

class VkSpider(BaseSpider):
    initial_urls = ['http://m.vk.com']

    def task_initial(self, grab, task):
        for account in self.meta['accounts']:
            login, password = account.split(":")
            grab.set_input("email", login)
            grab.set_input("pass", password)
            grab.submit(make_request=False)
            yield Task(name="login", grab=grab, account=account)


bot = VkSpider()
bot.run()
