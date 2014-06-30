import re
import random

RE_SCRIPT = re.compile(r'<script[^>]+recaptcha\.net[^>]+>', re.S)
RE_SCRIPT2 = re.compile(r'<script[^>]+google\.com/recaptcha/api/challenge[^>]+>', re.S)
RE_SCRIPT3 = re.compile(r'Recaptcha\.create\("([^"]+)', re.S | re.I)
RE_SRC = re.compile(r'src="([^"]+)"')

    #def solve_captcha(self, g, url=None, data=None):
        #if url:
            #logging.debug('Downloading captcha')
            #g.request(url=url)
            #data = g.response.body

        #logging.debug('Solving captcha')
        #solution = self.module.solve_captcha(key=self.key, data=data)

        #logging.debug('Captcha solved: %s' % solution)
        #return solution


    #def solve_recaptcha(self, g):
        #def fetch_challenge():
            #for x in xrange(5):
                #url = None
                #match = RE_SCRIPT.search(g.response.body)
                #if match:
                    #url = RE_SRC.search(match.group(0)).group(1)
                #if not url:
                    #match = RE_SCRIPT2.search(g.response.body)
                    #if match:
                        #url = RE_SRC.search(match.group(0)).group(1)
                #if not url:
                    #if 'google.com/recaptcha/api/js/recaptcha_ajax.js' in g.response.body:
                        ## It is type of google recaptcha
                        #match = RE_SCRIPT3.search(g.response.body)
                        #code = match.group(1)
                        #url = 'http://www.google.com/recaptcha/api/challenge'\
                              #'?k=%s&ajax=1&cachestop=%s' % (code, str(random.random()))
                        ##response = frame_loader.response.body
                        ##rex = re.compile(r"challenge : '[^\"\s]+',")
                        ##challenge_code = rex.search(response).group(0)[13:-2]
                        
                        ##image_loader = frame_loader.clone()
                        ##image_url = 'https://www.google.com/recaptcha/api/image?c=%s' % challenge_code
                        ##solution = solve_captcha(image_loader, url=image_url)

                #if not url:
                    #raise Exception('Unknown recaptcha implementation')

                #g.request(url=url)
                #html = g.response.body

                #if not html:
                    #logging.error('Empty response from recaptcha server')
                    #continue

                #server = re.compile(r'server\s*:\s*\'([^\']+)').search(html).group(1)
                #challenge = re.compile(r'challenge\s*:\s*\'([^\']+)').search(html).group(1)
                #url = server + 'image?c=' + challenge
                #return challenge, url
            #raise CaptchaError('Could not get valid response from recaptcha server')

        #challenge, url = fetch_challenge()
        #solution = self.solve_captcha(g, url=url)
        #return challenge, solution
