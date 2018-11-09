# author: Thiago da Cunha Borges e Zeus Olenchuk Ganimi


import sys
from time import sleep
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException

from db_declarative import Database, Price

start = datetime.now()


class Browser:
    def __init__(self):
        options = Options()
        options.add_argument('-headless')
        self.browser = webdriver.Firefox(
            executable_path=r'firefox/geckodriver',
            firefox_options=options
        )
        try:
            self.browser.get('http://veiculos.fipe.org.br/')
            self.browser.find_element_by_link_text('Consulta de Carros e Utilitários Pequenos').click()
        except Exception as err:
            sys.stderr.write(str(err))
            self.browser.close()
            self = Browser()

    @property
    def input_ref(self):
        return self.browser.find_element_by_xpath('//*[@id="selectTabelaReferenciacarro_chosen"]/div/div/input')

    @property
    def input_marca(self):
        return self.browser.find_element_by_xpath('//*[@id="selectMarcacarro_chosen"]/div/div/input')

    @property
    def input_modelo(self):
        return self.browser.find_element_by_xpath('//*[@id="selectAnoModelocarro_chosen"]/div/div/input')

    @property
    def input_ano(self):
        return self.browser.find_element_by_xpath('//*[@id="selectAnocarro_chosen"]/div/div/input')

    @property
    def option_ref(self):
        return self.browser.find_element_by_xpath('//*[@id="selectTabelaReferenciacarro"]/option')

    @property
    def option_marca(self):
        return self.browser.find_element_by_xpath('//*[@id="selectMarcacarro"]/option')

    @property
    def option_modelo(self):
        list = self.browser.find_element_by_xpath('//*[@id="selectAnoModelocarro"]/option')
        return list if list else self.option_modelo

    @property
    def option_ano(self):
        return self.browser.find_element_by_xpath('//*[@id="selectAnocarro"]/option')

    @property
    def search(self):
        return self.browser.find_element_by_id('buttonPesquisarcarro')

    @property
    def clear(self):
        return self.browser.find_element_by_id('buttonLimparPesquisarcarro')

    @property
    def select_ano_result(self) -> str:
        try:
            return self.browser \
                .find_element_by_xpath('//div[@id="selectAnocarro_chosen"]//ul[@class="chosen-results"]/li') \
                .get_attribute('innerHTML')
        except Exception as err:
            sys.stderr.write(str(err))
            return ''

    @property
    def search_result(self):
        return self.browser.find_elements_by_xpath('//div[@id="resultadoConsultacarroFiltros"]/table//td')

    @staticmethod
    def get_option_list(opt: list):
        return [o.get_attribute('innerHTML').replace('&amp;', '&') for o in opt if o.get_attribute('innerHTML') != '']

    @staticmethod
    def input_send_keys(input_text, keys: str):
        input_text.send_keys(keys, Keys.ENTER)

    @staticmethod
    def input_send_keys_with_arrow_down(input_text, keys: str):
        input_text.send_keys(keys, Keys.ARROW_DOWN, Keys.ENTER)

    def close(self):
        self.browser.quit()


class Application:
    def __init__(self):
        self.browser = Browser()
        self.database = Database()
        self.reference = None
        self.marca = None
        self.modelo = None
        self.ano = None

    def restart_browser(self):
        try:
            self.browser.browser.quit()
            del self.browser
            self.browser = Browser()
        except Exception as err:
            sys.stderr.write(str(err))
            sleep(60)
            self.restart_browser()

    def save_search(self):
        try:
            self.browser.search.click()
            info = self.browser.search_result

            self.modelo.fipe_code = info[3].text
            self.database.save_database(self.modelo)

            price = float(info[15].text.replace('R$ ', '').replace('.', '').replace(',', '.'))
            price = Price(id_referencia=self.reference.id, id_ano_modelo=self.ano.id, value=price)
            self.database.save_database(price)

            self.browser.clear.click()
            sleep(1)
        except ElementClickInterceptedException as err:
            sys.stderr.write(str(err))
            if self.browser.select_ano_result.startswith('Nada encontrado com'):
                self.database.delete_ano(self.ano.id)
            else:
                self.restart_browser()
            return False
        except (NoSuchElementException, IndexError, Exception) as err:
            sys.stderr.write(str(err))
            self.restart_browser()
            return False
        return True

    def select_ano(self):
        # esse if trata a interrupção do scraper.
        # a lista de veículos será salva no banco
        # apenas quando não houver nehuma ano visitado
        if not self.database.has_unvisited_ano():
            print(datetime.now(), datetime.now() - start, self.modelo.modelo_name)
            self.database.save_anos(
                self.browser.get_option_list(self.browser.option_ano),
                self.modelo.id,
                self.reference.period
            )

        # enquanto houver ano não visitado
        # executará esse laço
        while self.database.has_unvisited_ano():
            # seleciona o primeiro ano do veículo
            # não visitado do banco de dados
            self.ano = self.database.get_unvisited_ano(self.modelo.id)

            try:
                # seleciona referencia, marca modelo e ano do modelo
                self.browser.input_send_keys(self.browser.input_ref, self.reference.text)
                if self.marca.id == 73:
                    self.browser.input_send_keys_with_arrow_down(
                        self.browser.input_marca, self.marca.marca_name
                    )
                else:
                    self.browser.input_send_keys(self.browser.input_marca, self.marca.marca_name)
                self.browser.input_send_keys(self.browser.input_modelo, self.modelo.modelo_name)
                self.browser.input_send_keys(self.browser.input_ano, self.ano.ano_modelo)
            except Exception as err:
                sys.stderr.write(str(err))
                self.restart_browser()
            else:
                saved = self.save_search()
                if saved:
                    self.database.set_ano_visited(self.ano.id)

    def select_modelo(self):
        # esse if trata a interrupção do scraper.
        # a lista de veículos será salva no banco
        # apenas quando não houver nenhum modelo visitado
        if not self.database.has_unvisited_modelo():
            print(datetime.now() - start, self.marca.marca_name)
            self.database.save_modelos(self.browser.get_option_list(self.browser.option_modelo), self.marca.id)

        # enquanto houver modelos não visitados
        # no banco de dados executa esse laço
        while self.database.has_unvisited_modelo():
            # seleciona um modelo não visitado do banco de dados
            # atentando para o caso da marca Buggy que mudou de nome para Baby
            self.modelo = self.database.get_unvisited_modelo(self.marca.id if self.marca.id != 89 else 8)

            try:
                # sempre é feita a seleção de marca
                # pois após a consulta de um carro
                # todos os campos são apagados
                self.browser.input_send_keys(self.browser.input_ref, self.reference.text)
                if self.marca.id == 73:
                    self.browser.input_send_keys_with_arrow_down(self.browser.input_marca, self.marca.marca_name)
                else:
                    self.browser.input_send_keys(self.browser.input_marca, self.marca.marca_name)
                # selciona o modelo
                self.browser.input_send_keys(self.browser.input_modelo, self.modelo.modelo_name)
                sleep(2)  # aguarda o carregamento do ajax
            except Exception as err:
                sys.stderr.write(str(err))
                self.restart_browser()
            else:
                self.select_ano()

                self.database.set_modelo_visited(self.modelo.id)

    def select_marca(self):
        # esse if trata a interrupção do scraper.
        # a lista de veículos será salva no banco
        # apenas quando não houver nenhuma marca visitada
        if not self.database.has_marca_unvisited():
            print(datetime.now() - start, self.reference.text)
            self.database.save_marcas(self.browser.get_option_list(self.browser.option_marca), self.reference.id)

        # enquanto houver marcas não visitadas executará esse laço
        while self.database.has_marca_unvisited():
            self.marca = self.database.get_unvisted_marca(self.reference.id)
            # quando é feita a seleção da marca Rover,
            # estava sendo escolhida a marca Land Rover,
            # pois está se sobrepõe a primeira
            # por causa do select estar ordenado em ordem alfabética,
            # assim, é necessário enviar um comando de seta para baixo
            # para fazer a seleção correta da marca
            try:
                self.browser.input_send_keys(self.browser.input_ref, self.reference.text)
                if self.marca.id == 73:
                    self.browser.input_send_keys_with_arrow_down(self.browser.input_marca, self.marca.marca_name)
                else:
                    self.browser.input_send_keys(self.browser.input_marca, self.marca.marca_name)
                sleep(2)  # aguarda o load do ajax
            except Exception as err:
                sys.stderr.write(str(err))
                self.restart_browser()
            else:
                # seleciona todos
                # os modelos dessa marca
                self.select_modelo()
                # marca a marca de veículos
                # como visitada
                self.database.set_marca_visited(self.marca.id)

    def select_reference(self):
        # pega todos os valores presentes no campo período de referencia
        # e salva no banco de dados
        references = self.browser.get_option_list(self.browser.option_ref)
        self.database.save_reference(references)

        # enquanto houver período de referência no banco de dado
        # com o valor não visitado atribuído, executará esse laço
        while self.database.has_unvisited_reference():
            # pega a primeira referencia do banco de dados
            # e marca o campo período de referencia
            self.reference = self.database.get_unvisted_reference()
            self.browser.input_send_keys(self.browser.input_ref, self.reference.text)
            sleep(2)  # aguarda o load do ajax
            # faz a seleção de marcas
            # para a referencia determinada
            self.select_marca()
            # marca a referencia
            # como visitada
            self.database.set_reference_visited(self.reference.id)

    def run(self):
        self.select_reference()
        self.browser.close()


if __name__ == '__main__':

    app = Application()
    try:
        sleep(2)
        app.run()
    except Exception as e:
        sys.stderr.write(str(e))
        app.browser.close()
