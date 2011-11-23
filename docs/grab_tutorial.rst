.. _grab-quickstart:

Grab Tutorial
=============

In this lesson we will do some real things. Let's write the
bot which creates new account on bitbucket.org server and upload
avatar image::

    # First, import required things
    from grab import Grab, UploadFile
    import re
    import logging

    def main():
        # Create Grab instance
        g = Grab()

        # Configure logging
        # We want to see grab activity in the console
        logging.basicConfig(level=logging.DEBUG)

        # Configure it to save all requests and responses into
        # directory. Do not forget to create this directory.
        g.setup(log_dir='var/log')

        # Now go to bitubucket Sign Up page
        g.go('...')

        username = 'grab-tutorial'
        # We will use mailinator
        email = '%s@mailinator.com'

        while True:
            # Now we fill the form.
            g.set_input('username', username)
            g.set_input('password', 'test')
            g.set_input('email', email)
            
            # Submit the form
            # We do not bother about hidden fields.
            # If they exists then Grab will submit their
            # values automatically.
            # Also grab automatically detects the action 
            # url of the form and the encryption type.
            g.submit()

            # Let's check for form errors
            # g.css_list return lxml.etree.Element nodes which
            # match the given CSS query
            # You should learn lxml API to use Grab
            errors = ' '.join(x.text_content() for x in g.css_list('...'))
            if errors:
                if 'Username already exists':
                    # We should generate another username here
                    username = 'foobar'
            else:
                # Break the cycle if no errors
                break

        # Ok, now we should get the page with 
        # message about email activation
        # Lets's ensure that we are on this page
        grab.assert_substring('...')

        # Now go to mailinator, find the activation email
        # and extract link from it
        # It makes sense to do it with another Grab instance
        # Because first grab instance stores the bitbucket.org
        # session
        g2 = Grab()
        g2.go('...')
        ...
        ...

        # Now we have activation link and we can proceed
        # the sign up process on bitbucket
        g.go(activation_url)

        # Now go to Edit Profile page
        g.go('...')
        
        # Let's upload google logo image as profile image :)
        # First, we should download google logo
        g2 = Grab()
        g2.go('...')
        # We fetched google logo, now save it to the disk
        g2.response.save('/tmp/logo.jpg')

        # And upload it to bitbucket
        # Note that we start working with g instance
        # which "remembers" about bitbucket.org session cookies
        # and about the profile form which we are requested before we
        # started to work with google logo
        g.set_input('avatar', UploadFile('/tmp/logo.jpg'))
        g.submit()

        # That's all :)
