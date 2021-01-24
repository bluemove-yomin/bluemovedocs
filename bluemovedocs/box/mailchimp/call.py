from mailchimp_marketing import Client

mailchimp = Client()
mailchimp.set_config({
  "api_key": "259676fb403167451911d0065155d38a-us4",
  "server": "us4"
})

response = mailchimp.ping.get()
print(response)