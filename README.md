![App Screenshot](https://s1.hostingkartinok.com/uploads/images/2022/01/2d20913e1702ee4fd3618e0f72998aaa.png)

## Installation
**1) Download and enter to the project directory**
```bash
git clone https://github.com/The-Solomon/fb-parser.git
cd fb-parser
```
**2) Install all requirements from requirements.txt**
```bash
pip3 install -r requirements.txt
```
**3) Run parser**
```bash 

usage: python3 main.py -g [groups.txt] -k [keys.txt] -pl [UA PL] -f [result.txt]

Process some integers.

optional arguments:
  -h, --help            show this help message and exit
  -pl, --phone-location
                        Буквенный код страны в формате iso2 (по-умолчанию
                        только UA)
  -g, --group-list      Путь к файлу со списком групп которые нужно спарсить
  -k, --key-list        Путь к файлу со списком ключей поиска
  -f, --file            Имя файла в который вносятся результаты парсинга
  -t, --table           Выводить результаты парсинга в консоль
  -d, --deep            Расширенный парсинг, искать объявления в которых не
                        указан номер телефона
  --scroll              Количество экранов на которое программа опустит экран
                        браузера
  --pause               Количество секунд между скроллом

```
## Parsing result example
![Example](https://s1.hostingkartinok.com/uploads/images/2022/01/7e28e620bdddea6c899e4f29aeda11f5.png)