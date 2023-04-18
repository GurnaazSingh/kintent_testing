from flask import g, after_this_request


# def after_this_request(f):
# 	if not hasattr(g, 'after_request_callbacks'):
# 		g.after_request_callbacks = []
# 	g.after_request_callbacks.append(f)
# 	return f


@after_this_request
def generate_session_cookies(response):
	return response.set_cookies("access", "qwerty", httponly=True,SameSite=None,secure=True)
