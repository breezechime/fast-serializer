from fast_serializer.exceptions import ErrorDetail, DataclassCustomError

detail = ErrorDetail(key='key', loc=['loc'], input='input', exception_type='exception_type', msg='msg', ctx=None)
print(detail)

print(type(DataclassCustomError('asd', 'asd')) is DataclassCustomError)