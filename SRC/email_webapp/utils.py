from kavenegar import *


def send_otp_code(phone_number, code):
    try:
        api = KavenegarAPI('486A6A58756A6732373332546F5552387A3434593934566841487170614B46385545483273567152732B733D')
        params = {
            'sender': '',
            'receptor': phone_number,
            'message': f'{code} کد تایید شما '
        }
        response = api.sms_send(params)
        print(response)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)


def send_recover_link(phone_number, link):
    try:
        api = KavenegarAPI('486A6A58756A6732373332546F5552387A3434593934566841487170614B46385545483273567152732B733D')
        params = {
            'sender': '',
            'receptor': phone_number,
            'message': f'{link} Click here to recover your password '
        }
        response = api.sms_send(params)
        print(response)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)
