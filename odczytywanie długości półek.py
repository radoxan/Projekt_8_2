data_dict = info.model_dump()
number = data_dict['number_of_bends']

def create_image_info_model(number: int):
    fields = {f'length_{i+1}': (float, ...) for i in range(number)}
    return create_model('ImageInfo_2', **fields)

number = 3
ImageInfo_2 = create_image_info_model(number)

info_2 = instructor_openai_client.chat.completions.create(
    model="gpt-4o",
    response_model=ImageInfo_2,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Na rysunku technicznym znajduje się detal gięty z blachy. Odczytaj wymiary półek z rzutu przekroju. Znajdują się one w widoku przekroju. Ich ilość to {number}, jeżeli po wymiarze będzie minus albo plus nie uzględniach dlaszych cyfr, wszystkie długości są opisane na tym samym rzucie. Pamiętaj, że każda półka przylega do następnej i zazwyczaj po wymiarze poziomym będzie pionowy, następnie poziomy i tak dalej na zmianę. Wymiary wypisz w takiej samej kolejności.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": prepare_image_for_open_ai(f"{output_path}.png"),
                        "detail": "high"
                    },
                },
            ],
        },
    ],
    seed=1
)

print(info_2.model_dump())