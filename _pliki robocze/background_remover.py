from rembg import remove

input_path = 'd.jpg'
output_path = 'd_output.png'

with open(input_path, 'rb') as i:
    with open(output_path, 'wb') as o:
        input = i.read()
        output = remove(input, force_return_bytes=True)
        o.write(output)