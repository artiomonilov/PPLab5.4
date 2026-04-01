from main import MockMessageQueue  
try:  
    m = MockMessageQueue(1234)  
except Exception as e:  
    print(repr(e))  
m2 = MockMessageQueue(1234, 1)  
print('Done!')  
