def encrypt(password):
	#password=raw_input()
	protected=0
	for i in password:
		protected=(protected*1000)+ord(i)+384
	return str(protected)

def decrypt(nc):
	password=""
	code=int(nc)
	if len(nc)%3==0:
		n=int(len(nc)/3)
	else:
		n=int(len(nc)/3 +1)
	for i in range(n):
		password=chr(((code)%1000)%128)+password
		code=int(code/1000)
	return password


def is_correct(entered,encrypted):
	if(encrypt(entered)==encrypted):
		return True
	return  False


if __name__=="__main__":
	p=input()
	en=encrypt(p)
	de=decrypt(en)
	print ("encrypted form:",en)
	print ("decrypted form:",de)
	senthil=input()
	value=is_correct(senthil,encrypt(p))
	print (value)
	
