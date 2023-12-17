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
### Getting https to work with DNS forwarding
- Does not work the godaddy forwarding
- Instructions for `redirect.pizza` solution (no masking): https://redirect.pizza/support/godaddy-forwarding-with-https-support

### Cookie "Samesite" Error
Error message in browser console:
```
Cookie “session_id” does not have a proper “SameSite” attribute value. Soon, cookies without the “SameSite” attribute or with an invalid value will be treated as “Lax”. This means that the cookie will no longer be sent in third-party contexts. If your application depends on this cookie being available in such contexts, please add the “SameSite=None“ attribute to it. To know more about the “SameSite“ attribute, read https://developer.mozilla.org/docs/Web/HTTP/Headers/Set-Cookie/SameSite
```

Added `samesite=None` to `set_cookie()` call:
```
resp.set_cookie('session_id', session_id, expires=expire_date, samesite=None)
```

### CORS Error
Error message in browser console:
```
Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource at https://sudoku-bot-u4sp7ks5ea-uc.a.run.app/heartbeat. (Reason: CORS header ‘Access-Control-Allow-Origin’ missing). Status code: 200. 
https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSMissingAllowOrigin
```
Added this to response:
```
r = Response('Heartbeat', status=200)
r.headers['Access-Control-Allow-Origin'] = '*'
return r
```

### Bot icons
https://thenounproject.com/icon/thinking-ai-bot-1812244/








