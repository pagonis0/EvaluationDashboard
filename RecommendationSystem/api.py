import os, json
import requests
from requests.exceptions import HTTPError, RequestException
from configparser import ConfigParser
from flask import abort

from typing import Union
from urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.simplefilter('ignore', InsecureRequestWarning)


class MoodleAPI:

    def __init__(self):
        self.base_url = "https://success.thi.de/webservice/rest/server.php"
        self.ln_url_old = "?wstoken=38cb1aa68d55c4f2d8dcb691a306b2f6" \
                "&wsfunction=local_wstemplate_get_all_learning_nuggets" \
                "&moodlewsrestformat=json"
        self.ln_url_new = "?wstoken=38cb1aa68d55c4f2d8dcb691a306b2f6" \
                "&wsfunction=local_wstemplate_get_all_learning_nuggets_new" \
                "&moodlewsrestformat=json"
        self.lns_json = None
        #Added by Panos
        # From here #
        self.lns_stored = "/app/metadata_cache.json"
        # Till here #

    def _get_json(self, target_url) -> list:
        """
        Use GET call to moodle API.

        Get either list of all courses in Moodle or all Learning Nuggets, including their metadata, course assignment and section Id.
        Raises HTTPError if the response is an error message.
        :param tgt: (str) whether to get "courses" or "lns"
        :return: list of dicts, object resulting from call as json-like
        """
        #Added by Panos
        # From here #
        if target_url==self.lns_stored:
            with open(target_url, 'r') as file:
                response = json.load(file)
            return response
        else:
        # Till here #
            try:
                response = requests.get(self.base_url + target_url, verify=False)
                response.raise_for_status()
                return response.json()
            except HTTPError as err:
                print(f'HTTP error occurred: {err}')
                raise err

    def get_lns(self) -> dict:
        """
        Use GET call to get learning nuggets from moodle.

        :return: ln_dict, a dictionary mapping customfield_data_id from ln metadata to a dictionary with keys
                            "course_id", "course_name" (might change in future)
        """
        lns_json = self._get_json(self.lns_stored)
        # Commented out by Panos
        # From here #
        #lns_json = self._get_json(self.ln_url_old)
        #lns_json.extend(self._get_json(self.lns_stored))
        # Till here #
        self._check_mdl_request_exception(lns_json, "lns")

        ln_dict = {}
        # print(set([ln['section_base_info']['resp_id'] for ln in lns_json]))
        # Commented out by Panos
        # From here #
        #for ln in lns_json:
        #    if not (ln['meta_data_info'].get('Is the activity a Learning Nugget?', False) or ln['meta_data_info'].get('is_ln', False)):
        #        continue
        # Till here #

        # Added by Panos
        # From here #
        for ln_group in lns_json:
            for ln in ln_group:
                if not ln['meta_data_info'].get('is_ln', False):
                    continue
        # Till here (the whole code on indent inside) #

                if "Konvergierend" in ln['meta_data_info'].keys():
                    has_ls = (ln['meta_data_info']['Konvergierend'] or ln['meta_data_info']['Divergierend'] or
                            ln['meta_data_info']['Akkommodierend'] or ln['meta_data_info']['Assimilierend'])
                else:
                    #has_ls = (ln['meta_data_info']['example'] or ln['meta_data_info']['motivation'] or 
                    #          ln['meta_data_info']['explanation'] or ln['meta_data_info']['assignment'] or
                    #          ln['meta_data_info']['experiment'])
                    has_ls = True

                if has_ls:
                    if 'Category' not in ln['meta_data_info'] and "activitytopic" not in ln['meta_data_info']:
                        print(f"{ln['module_base_info']['content_name']} has no Category")
                        continue

                    if "Konvergierend" in ln['meta_data_info'].keys():
                        # Old Metadata Version
                        ln_dict[ln["meta_data_info"]["customfield_data_id"]] = \
                            {
                                "cm_id": ln['course_module_id'],
                                "course_id": ln['course_info']['id'],  # int
                                "course_name": ln['course_info']['fullname'],  # string
                                "ln_name": ln['module_base_info']['content_name'],  # string
                                "learning goal (LN)": ln['meta_data_info']['Learning Goal (Learning Nugget)'],  # str
                                "keywords": ln['meta_data_info']['Keywords'],  # str
                                "Konvergierend": ln['meta_data_info']['Konvergierend'],  # int
                                "Divergierend": ln['meta_data_info']['Divergierend'],  # int
                                "Akkommodierend": ln['meta_data_info']['Akkommodierend'],  # int
                                "Assimilierend": ln['meta_data_info']['Assimilierend'],  # int
                                "example": 0,
                                "motivation": 0,
                                "explanation": 0,
                                "assignment": 0,
                                "experiment": 0,
                                "category": ln['meta_data_info']['Category'],  # str
                                "subcategory": ln['meta_data_info']['Sub-category'],  # TODO
                                "difficulty": ln['meta_data_info']['Difficulty'].strip(),  # str
                                "mid": ln['module_base_info']['id'],  # int
                                "mname": ln['module_base_info']['name'],  # str
                                "mvisible": ln['module_base_info']['visible'],  # int
                                "section_id": ln['section_base_info']['resp_id'],  # int
                                "section_name": ln['section_base_info']['name'],  # str
                                "course_section": ln['section_base_info']['course_section'],  # str(int)
                                "contenttype": None,
                            }
                        if 'Prerequisites' in ln['meta_data_info']:
                            ln_dict[ln["meta_data_info"]["customfield_data_id"]]["prerequisites"] = ln['meta_data_info']['Prerequisites'].strip()
                        else:
                            ln_dict[ln["meta_data_info"]["customfield_data_id"]]["prerequisites"] = None
                    else:
                        # New Metadata Version (currently in staging only)
                        example = ln['meta_data_info'].get("example", 0)
                        motivation = ln['meta_data_info'].get("motivation", 0)
                        explanation = ln['meta_data_info'].get("explanation", 0)
                        assignment = ln['meta_data_info'].get("assignment", 0)
                        experiment = ln['meta_data_info'].get("experiment", 0)
                        if not (example == 1 or  motivation == 1 or explanation == 1 or assignment == 1 or experiment == 1):
                            motivation = 1
                        ln_dict[ln["meta_data_info"]["id"]] = \
                        {
                            "cm_id": ln['course_module_id'],
                            "course_id": ln['course_info']['id'],  # int
                            "course_name": ln['course_info']['fullname'],  # string
                            "ln_name": ln['module_base_info']['content_name'],  # string
                            "learning goal (LN)": None,  # str
                            "keywords": ln['meta_data_info']['keywords'],  # str
                            "Konvergierend": 0,  # int
                            "Divergierend": 0,  # int
                            "Akkommodierend": 0,  # int
                            "Assimilierend": 0,  # int
                            "example": example if example is not None else 0,  # int
                            "motivation": motivation if motivation is not None else 0,  # int
                            "explanation": explanation if explanation is not None else 0,  # int
                            "assignment": assignment if assignment is not None else 0,  # int
                            "experiment": experiment if experiment is not None else 0,  # int
                            "category": ln['meta_data_info']['activitytopic'],  # str
                            "subcategory": None,  # TODO
                            "difficulty": ln['meta_data_info']['difficulty'].strip(),  # str
                            "mid": ln['module_base_info']['id'],  # int
                            "mname": ln['module_base_info']['name'],  # str
                            "mvisible": ln['module_base_info']['visible'],  # int
                            "section_id": ln['section_base_info']['resp_id'],  # int
                            "section_name": ln['section_base_info']['name'],  # str
                            "course_section": ln['section_base_info']['course_section'],  # str(int)
                        }
                        if 'prerequisites' in ln['meta_data_info']:
                            ln_dict[ln["meta_data_info"]["id"]]["prerequisites"] = ln['meta_data_info']['prerequisites'].strip()
                        else:
                            ln_dict[ln["meta_data_info"]["id"]]["prerequisites"] = None
            return ln_dict

    def _check_mdl_request_exception(self, json: Union[dict, list], tgt: str):
        """
        Check if a call response is an error message and raise a RequestException if that is the cases.

        :param json: (Union(list, dict)) response from API call as json
        :param tgt: (str) whether request was for "courses" or "lns"
        """
        if (type(json) == dict) and ('exception' in json.keys()):
            raise RequestException(
                f"Moodle API call for {tgt} caused {json['exception']}."
                f" Error code: {json['errorcode']}."
                f" Message: {json['message']}"
            )
        
    def _get_lns(self, update=False):
        if update or not os.path.isfile("/app/data/lns.json"):
            self.lns_json = self.get_lns()
            with open("/app/lns.json", "w") as jfile:
                json.dump(self.lns_json, jfile, indent=2)
        else:
            with open("/app/lns.json", "r") as jfile:
                self.lns_json = json.load(jfile)
            self.lns_json = {int(key): value for key, value in self.lns_json.items()}

        cmid2lnid = {str(entry["cm_id"]): ln_id for ln_id, entry in self.lns_json.items()}

        course_table = []
        lns_table = [["ID", "Name", "Moodle", "Course ID", "Course", "Category", "Section ID", "Section", ""]]
        for key, entry in self.lns_json.items():
            lns_table.append([key, entry["ln_name"],
                            f"https://success.thi.de/mod/{entry['mname']}/view.php?id={entry['cm_id']}",
                            entry["course_id"], entry["course_name"], entry["category"],
                            entry["section_id"], entry["section_name"],
                            "added"])
            course_table.append((entry["course_id"], entry["course_name"], "enrolled"))
        course_table = list(set(course_table))
        course_table.insert(0, ["ID", "Name", ""])

        return self.lns_json, lns_table, cmid2lnid, course_table


    def _get_post(self, ln_id):
        ln = self.lns_json.get(str(ln_id), None)

        if ln is None:
            abort(404)
        return ln


class RecommenderAPI:

    def __init__(self):
        config = ConfigParser()
        assert os.path.exists("config.ini")
        config.read("config.ini")
        self.url = config['SERVER']['url']
        self.token = config['SERVER']['token']

    def get_recommendation(self, query):
        try:
            response = requests.post(self.url, json=query,
                                     headers={'Authorization': f'Bearer {self.token}'})
            response.raise_for_status()
            return response.json()
        except HTTPError as err:
            print(f'HTTP error occurred: {err}')
            raise err
