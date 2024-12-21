import requests
import json
import time
import re
from lxml import etree

root = etree.Element('Ads', version="3.0", target="Avito.ru")

from headers_and_json import headers
from get_ids import get_ids

base_url = "https://api.investmoscow.ru/investmoscow/tender/v1/object-info/gettenderobjectinformation?tenderId="
Space_pattern = r"^[0-9]{1,}\,[0-9]{1,}|^[0-9]{1,}"
Ids = get_ids()
count = 0
for i in Ids:
    time.sleep(1)
    response = requests.get(
        base_url + str(i),
        headers=headers
    )
    apartment = json.loads(response.text)

    info = {
        "Id": apartment["tenderId"],
        "Description": "",
        "Address": apartment["headerInfo"]["address"],
        "OperationType": "Продам",
        "Category": "Квартиры",
        "Status": "Квартира",
        "BalconyOrLoggiaMulti": [],
        "Images": [],
        "SaleOptions": "Аукцион",
        "MarketType": "Вторичка",
        "PropertyRights": "Посредник",
        "DealType": "Прямая продажа",
    }

    description_info = {}

    for a in apartment["objectInfo"]:
        match a["label"]:
            case "Площадь кухни":
                info["KitchenSpace"] = re.findall(Space_pattern, a["value"])[0]
            case "Площадь жилая":
                info["LivingSpace"] = re.findall(Space_pattern, a["value"])[0]
            case "Наличие лоджии":
                if a["value"] == "Да":
                    info["BalconyOrLoggiaMulti"].append("Лоджия")
            case "Наличие балкона":
                if a["value"] == "Да":
                    info["BalconyOrLoggiaMulti"].append("Балкон")
            case "Этажность дома":
                info["Floors"] = a["value"]
            case "Этаж":
                info["Floor"] = a["value"]
            case "Кадастровый номер":
                description_info["Cadastral_number"] = a["value"]
            case "Количество комнат":
                info["Rooms"] = a["value"]
            case "Площадь объекта":
                info["Square"] = re.findall(Space_pattern, a["value"])[0]           

    for a in apartment["procedureInfo"]:
        match a["label"]:
            case "Начальная цена за объект":
                info["Price"] = ''.join(a["value"].split(' ')[0].replace('.', ' ').replace(',', ' ').split())
                description_info["Price"] = a["value"]
            case "Размер задатка":
                description_info["Deposit"] = a["value"]
            case "Шаг аукциона":
                description_info["Auction_step"] = a["value"]
            case "Форма проведения":
                description_info["form_of_auction"] = a["value"]
            case "Дата начала приёма заявок":
                description_info["DateBegin"] = a["value"]
            case "Дата окончания приёма заявок":
                description_info["DateEnd"] = a["value"]
                info["DateEnd"] = a["value"]
            case "Отбор участников":
                description_info["selection"] = a["value"]
            case "Проведение торгов":
                description_info["Bidding"] = a["value"]
            case "Подведение итогов":
                description_info["Summing_up"] = a["value"]
    
    for a in apartment["imageInfo"]["attachedImages"]:
        info["Images"].append(a["url"])

    count += 1
    if info['Rooms'] == 'Не указано':
        print(f"Парсинг страницы {count} не завершён (Не указано поле Rooms)!")
        continue
    

    info["Description"] = f"""
    {info['Address']}

    Функциональное назначение: Жилое

    Площадь квартиры: {info['Square']} м2

    Тип входа: Вход через подъезд

    Этажность дома: {info['Floors']}

    Этаж: {info['Floor']}

    Количество комнат: {info['Rooms']}

    Кадастровый номер: {description_info['Cadastral_number']}

    Начальная цена за объект: {info['Price']} руб

    Размер задатка: {description_info['Deposit']}

    Шаг аукциона: {description_info['Auction_step']}

    Дата начала приёма заявок: {description_info['DateBegin']}

    Дата окончания приёма заявок: {info["DateEnd"]}

    Отбор участников: {description_info["selection"]}

    Проведение торгов: {description_info['Bidding']}

    Подведение итогов: {description_info['Summing_up']}

    КВАРТИРА РЕАЛИЗУЕТСЯ НА ТОРГАХ ОТ ГОРОДА МОСКВЫ согласно закону 223-ФЗ, УКАЗАННАЯ ЦЕНА ЯВЛЯЕТСЯ СТАРТОВОЙ

    Полное юридическое сопровождение от подачи заявки на торги до подписания договора купли-продажи и получения документов на собственность.

    Являюсь сертифицированным экспертом по недвижимости и аттестованным брокером. Работаю с Вами по официальному договору.

    Продавец город Москва. В продаже от города сейчас есть разные объекты в Москве и области. Звоните, приходите на бесплатную консультацию
    """
    ad = etree.Element('Ad')
    
    for key in info:
        if key == "Images" and info[key] != []:
            images = etree.Element('Images')
            for i in info[key]:
                images.append(etree.Element('Image', url=i))
            ad.append(images)
        if key == "BalconyOrLoggiaMulti":
            BalconyOrLoggiaMulti = etree.Element('BalconyOrLoggiaMulti')
            if info[key] == []:
                etree.SubElement(BalconyOrLoggiaMulti, 'Option').text = 'Балкон'
            for i in info[key]:
                etree.SubElement(BalconyOrLoggiaMulti, 'Option').text = str(i)
            ad.append(BalconyOrLoggiaMulti)
            etree.SubElement(ad, 'HouseType').text = "Кирпичный"
        else:
            etree.SubElement(ad, key).text = str(info[key])
    if int(info["Rooms"]) >= 2 :
        etree.SubElement(ad, 'RoomType').text = 'Изолированные'
    root.append(ad)

    print(f"Парсинг объекта {count}/{len(Ids)} завершён")

with open("output.xml", "w", encoding='utf-8') as f:
    f.write(etree.tostring(root, pretty_print=True, encoding='utf-8').decode())