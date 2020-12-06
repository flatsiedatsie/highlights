"""Highlights API handler."""



import os
from os import path
import sys
sys.path.append(path.join(path.dirname(path.abspath(__file__)), 'lib'))
import json
import time
from time import sleep
import requests
import threading

try:
    from gateway_addon import APIHandler, APIResponse, Adapter, Device, Property, Database
    #print("succesfully loaded APIHandler and APIResponse from gateway_addon")
except:
    print("Import APIHandler and APIResponse from gateway_addon failed. Use at least WebThings Gateway version 0.10")
    sys.exit(1)


_TIMEOUT = 3

_CONFIG_PATHS = [
    os.path.join(os.path.expanduser('~'), '.webthings', 'config'),
]

if 'WEBTHINGS_HOME' in os.environ:
    _CONFIG_PATHS.insert(0, os.path.join(os.environ['WEBTHINGS_HOME'], 'config'))



class HighlightsAPIHandler(APIHandler):
    """Highlights API handler."""

    def __init__(self, verbose=False):
        """Initialize the object."""
        #print("INSIDE API HANDLER INIT")
        
        
        self.addon_name = 'highlights'
        self.running = True

        self.server = 'http://127.0.0.1:8080'
        self.DEV = True
        self.DEBUG = False
            
        self.things = [] # Holds all the things, updated via the API. Used to display a nicer thing name instead of the technical internal ID.
        self.data_types_lookup_table = {}
        self.token = None
        

        
        # LOAD CONFIG
        try:
            self.add_from_config()
        except Exception as ex:
            print("Error loading config: " + str(ex))

        
        # Get complete things dictionary via API
        try:
            self.things = self.api_get("/things")
            #print("Did the things API call. Self.things is now:")
            #print(str(self.things))

        except Exception as ex:
            print("Error getting updated things data via API: " + str(ex))
        
        
        
        # temporary moving of persistence files   
        old_location = os.path.join(os.path.expanduser('~'), '.mozilla-iot', 'data', self.addon_name,'persistence.json')
        new_location = os.path.join(os.path.expanduser('~'), '.webthings', 'data', self.addon_name,'persistence.json')
        
        if os.path.isfile(old_location) and not os.path.isfile(new_location):
            print("moving persistence file to new location: " + str(new_location))
            os.rename(old_location, new_location)
        
        
        # Paths
        # Get persistent data
        try:
            #print("self.user_profile['dataDir'] = " + str(self.user_profile))
            self.persistence_file_path = os.path.join(self.user_profile['dataDir'], self.addon_name, 'persistence.json')
        except:
            try:
                if self.DEBUG:
                    print("setting persistence file path failed, will try older method.")
                self.persistence_file_path = os.path.join(os.path.expanduser('~'), '.webthings', 'data', self.addon_name,'persistence.json')
            except:
                if self.DEBUG:
                    print("Double error making persistence file path")
                self.persistence_file_path = "/home/pi/.webthings/data/" + self.addon_name + "/persistence.json"
        
        if self.DEBUG:
            print("Current working directory: " + str(os.getcwd()))
        
        
        first_run = False
        try:
            with open(self.persistence_file_path) as f:
                self.persistent_data = json.load(f)
                if self.DEBUG:
                    print("Persistence data was loaded succesfully.")
                
        except:
            first_run = True
            print("Could not load persistent data (if you just installed the add-on then this is normal)")
            self.persistent_data = {'items':[]}
            
        if self.DEBUG:
            print("Highlights self.persistent_data is now: " + str(self.persistent_data))


        try:
            self.adapter = HighlightsAdapter(self,verbose=False)
            #self.manager_proxy.add_api_handler(self.extension)
            #print("ADAPTER created")
        except Exception as e:
            print("Failed to start ADAPTER. Error: " + str(e))
        
        
        
        
        # Is there user profile data?    
        #try:
        #    print(str(self.user_profile))
        #except:
        #    print("no user profile data")
                

            
            
        # Intiate extension addon API handler
        try:
            manifest_fname = os.path.join(
                os.path.dirname(__file__),
                '..',
                'manifest.json'
            )

            with open(manifest_fname, 'rt') as f:
                manifest = json.load(f)

            APIHandler.__init__(self, manifest['id'])
            self.manager_proxy.add_api_handler(self)
            

            if self.DEBUG:
                print("self.manager_proxy = " + str(self.manager_proxy))
                print("Created new API HANDLER: " + str(manifest['id']))
        
        except Exception as e:
            print("Failed to init UX extension API handler: " + str(e))

        

        # Respond to gateway version
        try:
            if self.DEBUG:
                print(self.gateway_version)
        except:
            print("self.gateway_version did not exist")

        # Start the internal clock
        if self.DEBUG:
            print("Starting the internal clock")
        try:            
            t = threading.Thread(target=self.clock)
            t.daemon = True
            t.start()
        except:
            print("Error starting the clock thread")




    # Read the settings from the add-on settings page
    def add_from_config(self):
        """Attempt to read config data."""
        try:
            database = Database(self.addon_name)
            if not database.open():
                print("Could not open settings database")
                return
            
            config = database.load_config()
            database.close()
            
        except:
            print("Error! Failed to open settings database.")
        
        if not config:
            print("Error loading config from database")
            return
        
        
        
        # Api token
        try:
            if 'Authorization token' in config:
                self.token = str(config['Authorization token'])
                print("-Authorization token is present in the config data.")
        except:
            print("Error loading api token from settings")
        

        if 'Debugging' in config:
            self.DEBUG = bool(config['Debugging'])
            if self.DEBUG:
                print("-Debugging preference was in config: " + str(self.DEBUG))







#
#  CLOCK
#

    def clock(self):
        """ Runs every second """
        while self.running:
            time.sleep(1)
            try:
                for item in self.persistent_data['items']:
                    #print(str(item))
                    if 'thing1' in item and 'property1' in item and 'thing1_atype' in item and 'property1_atype' in item and 'enabled' in item:
                        
                        if bool(item['enabled']) == False:
                            continue
                            
                        api_get_result = self.api_get( '/things/' + str(item['thing1']) + '/properties/' + str(item['property1']))
                        #print("api_get_result = " + str(api_get_result))
                    
                        try:
                            key = list(api_get_result.keys())[0]
                        except:
                            print("error parsing the returned json")
                            #continue
                    
                        try:
                            if key == "error": 
                                if api_get_result[key] == 500:
                                    print("API GET failed (500 - thing not currently connected)")
                                    #pass
                                    #return

                            else:
                                #print("API GET was succesfull")
                                original_value = api_get_result[key]
                                if self.DEBUG:
                                    print("got this original value from API: " + str(original_value))
                            
                            
                                if original_value is "" or original_value is None:
                                    #print("original value is an empty string.") # this happens if the gateway has just been rebooted, and the property doesn not have a value yet.
                                    continue
                                    

                                if 'previous_value' not in item:
                                    item['previous_value'] = None

                                
                                try:
                                    if str(item['previous_value']) != str(original_value):
                                        #print("new value")
                                        #print("get_devices = " + str(self.adapter.get_devices()))
                                        targetDevice = self.adapter.get_device( "highlights-" + str(item['thing1']) + "-" + str(item['property1']) ) # targetDevice will be 'None' if it wasn't found.
                                        if targetDevice == None:
                                            if self.DEBUG:
                                                print("target device did not exist yet: " + str(item['thing1']) )
                                            
                                            
                                            # figure out optimal thing and property type
                                            try:
                                                #print("self.things = " + str(self.things))
                                                for thing in self.things:
                                                    thing_id = str(thing['id'].rsplit('/', 1)[-1])
                                                    #print("__id: " + str(thing_id))
                                                    if str(item['thing1']) == thing_id:
                                                        #print("thing1 was thing_id at: " + str(thing_id))
                                                        #print("thing['properties'] = " + str(thing['properties']))
                                                        for thing_property_key in thing['properties']:
                                                            
                                                            property_id = thing['properties'][thing_property_key]['links'][0]['href'].rsplit('/', 1)[-1]
                                                            if str(item['property1']) == property_id:
                                                                #print("full property: " + str(thing['properties'][thing_property_key]))
                                                                #print("___type: " + str(thing['properties'][thing_property_key]['type']))

                                                                #if '@type' in thing['properties'][thing_property_key]:
                                                                #    print("___atype: " + str(thing['properties'][thing_property_key]['@type']))
                                                            
                                                                clone_property = thing['properties'][thing_property_key].copy()
                                                                clone_property['@type'] = item['property1_atype']
                                                                
                                                                if not clone_property['links'][0]['href'].startswith("/things/highlights-"):
                                                                    new_href = clone_property['links'][0]['href'].replace("/things/","/things/highlights-")
                                                                    clone_property['links'][0]['href'] = new_href
                                                                
                                                                new_thing_title = "highlights " + str(item['thing1'])
                                                                if 'title' in thing:
                                                                    new_thing_title = "highlights " + str(thing['title'])
                                                                elif 'label' in thing:
                                                                    new_thing_title = "highlights " + str(thing['label'])
                                                            
                                                                new_thing_id = "highlights-" + str(item['thing1']) + '-' + str(item['property1'])
                                                            
                                                                device = HighlightsDevice(self, self.adapter, new_thing_id, new_thing_title, item['thing1_atype']) # note that it's wrapped in an array
                                                                self.adapter.handle_device_added(device)
                                                                targetDevice = self.adapter.get_device(new_thing_id)
                                                                
                                                                if targetDevice != None:
                                                                    if self.DEBUG:
                                                                        print("Creating cloned property. It's original_value will be: " + str(original_value))
                                                                    targetDevice.properties[ str(item['property1']) ] = HighlightsProperty(
                                                                                                    targetDevice,
                                                                                                    str(item['property1']),
                                                                                                    clone_property,
                                                                                                    original_value,
                                                                                                    str(item['thing1']),
                                                                                                    str(item['property1']) )
                                                                                
                                                                    targetProperty = targetDevice.find_property( str(item['property1']) )
                                                                    self.adapter.handle_device_added(device)
                                                                    targetProperty.update(original_value)
                                                                    targetDevice.notify_property_changed(targetProperty)
                                                                else:
                                                                    print("Error: the target device was still None after just creating it.")
                                                                
                                            except Exception as ex:
                                                print("Error creating new thing: " + str(ex))      
                                        
                                        try:
                                            if targetDevice != None:
                                                targetProperty = targetDevice.find_property( str(item['property1']) )
                                                if targetProperty != None:
                                                    targetProperty.update(original_value)
                                                else:
                                                    if self.DEBUG:
                                                        print("Error: missing property wasn't created?")
                                            else:
                                                if self.DEBUG:
                                                    print("Error: missing device wasn't created?")
                                            
                                        except Exception as ex:
                                            print("Error updating property: " + str(ex))

                                    
                                except Exception as ex:
                                    print("Error finding and updating property: " + str(ex))
                                    continue
                                    
                                        
                        except Exception as ex:
                            print("Error putting via API: " + str(ex))

            except Exception as ex:
                print("Clock error: " + str(ex))              
                        
                        

#
#  HANDLE REQUEST
#

    def handle_request(self, request):
        """
        Handle a new API request for this handler.

        request -- APIRequest object
        """
        
        try:
        
            if request.method != 'POST':
                return APIResponse(status=404)
            
            if request.path == '/init' or request.path == '/update_items':

                try:
                    
                    if request.path == '/init':
                        if self.DEBUG:
                            print("Getting the initialisation data")
                            
                        try:
                            state = 'ok'
        
                            # Check if a token is present
                            if self.token == None:
                                state = 'This addon requires an authorization token to work. Visit the settings page of this addon to learn more.'


                            return APIResponse(
                                status=200,
                                content_type='application/json',
                                content=json.dumps({'state' : state, 'items' : self.persistent_data['items']}),
                            )
                        except Exception as ex:
                            print("Error getting init data: " + str(ex))
                            return APIResponse(
                                status=500,
                                content_type='application/json',
                                content=json.dumps({'state' : "Internal error: no thing data", 'items' : []}),
                            )
                            
                    
                    elif request.path == '/update_items':
                        try:
                            self.persistent_data['items'] = request.body['items']
                            
                            
                            #print("")
                            # Get all the things via the API.
                            try:
                                self.things = self.api_get("/things")
                                #print("Did the things API call")
                            except Exception as ex:
                                print("Error getting updated things data via API: " + str(ex))
                                
                            # try to get the correct property type (integer/float)
                            try:
                                for item in self.persistent_data['items']:
                                    #print("_item: " + str(item))
                                    if 'thing1' in item and 'property1' in item:
                                        
                                        try:
                                            for thing in self.things:
                                                thing_id = str(thing['id'].rsplit('/', 1)[-1])
                                                
                                                if str(item['thing1']) == thing_id:
                                                    #print("__id SPOTTED: " + str(thing_id))
                                                    try:
                                                        #print("thing = " + str(thing))
                                                        potential_atype = None
                                                        #print("Thing = " + str(thing))
                                                        #if '@type' in thing:
                                                        try:
                                                            if hasattr(thing, '@type'):
                                                                #print("existing @type spotted in thing")
                                                                if len(thing['@type']) == 1:
                                                                    potential_atype = str(thing['@type'][0])
                                                                    
                                                        except Exception as ex:
                                                            print("Error checking for @type in thing: " + str(ex))
                                                            
                                                        #print("thing['properties'] = " + str(thing['properties']))
                                                            
                                                        for thing_property_key in thing['properties']:
                                            
                                                            property_id = thing['properties'][thing_property_key]['links'][0]['href'].rsplit('/', 1)[-1]
                                                            if self.DEBUG:
                                                                print("property_id = " + str(property_id))
                                                            if str(item['property1']) == property_id:
                                                                try:
                                                                    #print("full property: " + str(thing['properties'][thing_property_key]))

                                                                    done = False
                                                                    item['property1_type'] = str(thing['properties'][thing_property_key]['type'])
                                                            
                                                                    if '@type' in thing['properties'][thing_property_key]:
                                                                        if potential_atype != None:
                                                                            # Cloning a property that already has a capability
                                                                            #print("___atype: " + str(thing['properties'][thing_property_key]['@type']))
                                                                            item['thing1_atype'] = potential_atype
                                                                            item['property1_atype'] = str(thing['properties'][thing_property_key]['@type'])
                                                                            done = True
                                                                        else:
                                                                            atype = str(thing['properties'][thing_property_key]['@type'])

                                                                            if atype == 'AlarmProperty':
                                                                                item['thing1_atype'] = 'Alarm'
                                                                                item['property1_atype'] = atype
                                                                                done = True
                                                                            elif atype == 'OpenProperty':
                                                                                item['thing1_atype'] = 'DoorSensor'
                                                                                item['property1_atype'] = atype
                                                                                done = True
                                                                            elif atype == 'LockedProperty':
                                                                                item['thing1_atype'] = 'Lock'
                                                                                item['property1_atype'] = atype
                                                                                done = True
                                                                            elif atype == 'MotionProperty':
                                                                                item['thing1_atype'] = 'MotionSensor'
                                                                                item['property1_atype'] = atype
                                                                                done = True
                                                                            #elif atype == 'BrightnessProperty': # doesn't work, creates a boolean
                                                                            #    item['thing1_atype'] = 'Light'
                                                                            #    item['property1_atype'] = atype
                                                                            #    done = True
                                                                                
                                                                                
                                                                        # Todo: we could look up the corresponding thing @type if a property @type is provided.
                                                                    if done == False:
                                                                        # here we figure out a fitting capabiliy if the property doesn't have one yet. This is required for it to show up as the highlighted property.
                                                                
                                                                        if item['property1_type'] == 'number' or item['property1_type'] == 'integer':
                                                                            item['property1_atype'] = 'LevelProperty'
                                                                            item['thing1_atype'] = 'MultiLevelSensor'
                                                                            if 'unit' in thing['properties'][thing_property_key]:
                                                                                if thing['properties'][thing_property_key]['unit'].lower() == 'watt': # or thing['properties'][thing_property_key]['unit'].lower() == 'kwh':
                                                                                    if self.DEBUG:
                                                                                        print("spotted a kwh or watt") 
                                                                                    # technically using kwh is wrong here. But hey, I want that icon!
                                                                                    item['property1_atype'] = 'InstantaneousPowerProperty'
                                                                                    item['thing1_atype'] = 'EnergyMonitor'
                                                                            
                                                                        if item['property1_type'] == 'boolean':
                                                                            item['property1_atype'] = 'OnOffProperty'
                                                                            item['thing1_atype'] = 'OnOffSwitch'
                                                                            if 'readOnly' in thing['properties'][thing_property_key]:
                                                                                if bool(thing['properties'][thing_property_key]['readOnly']) == True:
                                                                                    item['property1_atype'] = 'BooleanProperty'
                                                                                    item['thing1_atype'] = 'BinarySensor'
                                        
                                                                    if self.DEBUG:
                                                                        print("item['thing1_atype'] has been deduced as: " + str(item['thing1_atype']))
                                                                        print("item['property1_atype'] has been deduced as: " + str(item['property1_atype']))
                                                                    
                                                                except Exception as ex:
                                                                    print("Error while analysing properties: " + str(ex))
                                                                
                                                    except Exception as ex:
                                                        print("Error while checking for @type in thing: " + str(ex))
                                        
                                        
                                        except Exception as ex:
                                            print("Error while while looping over things: " + str(ex))
                                            continue

                                        
                            except Exception as ex:
                                print("Error finding if property should be int or float: " + str(ex))
                            
                            self.save_persistent_data()
                            
                            return APIResponse(
                                status=200,
                                content_type='application/json',
                                content=json.dumps({'state' : 'ok'}),
                            )
                        except Exception as ex:
                            print("Error saving updated items: " + str(ex))
                            return APIResponse(
                                status=500,
                                content_type='application/json',
                                content=json.dumps("Error updating items: " + str(ex)),
                            )
                        
                    else:
                        return APIResponse(
                            status=500,
                            content_type='application/json',
                            content=json.dumps("API error"),
                        )
                        
                        
                except Exception as ex:
                    print("Init issue: " + str(ex))
                    return APIResponse(
                        status=500,
                        content_type='application/json',
                        content=json.dumps("Error in API handler"),
                    )
                    
            else:
                return APIResponse(status=404)
                
        except Exception as e:
            print("Failed to handle UX extension API request: " + str(e))
            return APIResponse(
                status=500,
                content_type='application/json',
                content=json.dumps("API Error"),
            )


    def unload(self):
        self.running = False
        if self.DEBUG:
            print("Highlights api handler shutting down")




    #def cancel_pairing(self):
    #    """Cancel the pairing process."""

        # Get all the things via the API.
    #    try:
    #        self.things = self.api_get("/things")
    #        #print("Did the things API call")
    #    except Exception as ex:
    #        print("Error, couldn't load things at init: " + str(ex))




#
#  API
#

    def api_get(self, api_path):
        """Returns data from the WebThings Gateway API."""
        if self.DEBUG:
            print("GET PATH = " + str(api_path))
        #print("GET TOKEN = " + str(self.token))
        if self.token == None:
            print("PLEASE ENTER YOUR AUTHORIZATION CODE IN THE SETTINGS PAGE")
            return []
        
        try:
            r = requests.get(self.server + api_path, headers={
                  'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'Bearer ' + str(self.token),
                }, verify=False, timeout=5)
            #if self.DEBUG:
            #    print("API GET: " + str(r.status_code) + ", " + str(r.reason))

            if r.status_code != 200:
                if self.DEBUG:
                    print("API GET returned a status code that was not 200. It was: " + str(r.status_code))
                return {"error": r.status_code}
                
            else:
                #if self.DEBUG:
                #    print("API get succesfull: " + str(r.text))
                return json.loads(r.text)
            
        except Exception as ex:
            print("Error doing " + str(api_path) + " request/loading returned json: " + str(ex))
            #return [] # or should this be {} ? Depends on the call perhaps.
            return {"error": 500}


    def api_put(self, api_path, json_dict):
        """Sends data to the WebThings Gateway API."""

        if self.DEBUG:
            print("PUT > api_path = " + str(api_path))
            print("PUT > json dict = " + str(json_dict))
            #print("PUT > self.server = " + str(self.server))
            #print("PUT > self.token = " + str(self.token))
            

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.token),
        }
        try:
            r = requests.put(
                self.server + api_path,
                json=json_dict,
                headers=headers,
                verify=False,
                timeout=3
            )
            #if self.DEBUG:
            #print("API PUT: " + str(r.status_code) + ", " + str(r.reason))

            if r.status_code != 200:
                #if self.DEBUG:
                #    print("Error communicating: " + str(r.status_code))
                return {"error": str(r.status_code)}
            else:
                if self.DEBUG:
                    print("API PUT response: " + str(r.text))
                return json.loads(r.text)

        except Exception as ex:
            print("Error doing http request/loading returned json: " + str(ex))
            #return {"error": "I could not connect to the web things gateway"}
            #return [] # or should this be {} ? Depends on the call perhaps.
            return {"error": 500}



#
#  Delete a thing
#

    def delete_thing(self, device_id):
        if self.DEBUG:
            print("Deleting a highlighted thing")
        try:
            for i in range(len(self.persistent_data['items'])): 
                if 'thing1' in self.persistent_data['items'][i]:
                    if str(device_id) == 'highlights-' + str(self.persistent_data['items'][i]['thing1']):
                        del self.persistent_data['items'][i]
                        self.save_persistent_data()
                        break
    
        except Exception as ex:
            print("Error removing highligh thing from persistence data: " + str(ex))


#
#  SAVE TO PERSISTENCE
#

    def save_persistent_data(self):
        #if self.DEBUG:
        print("Saving to persistence data store at path: " + str(self.persistence_file_path))
            
        try:
            if not os.path.isfile(self.persistence_file_path):
                open(self.persistence_file_path, 'a').close()
                if self.DEBUG:
                    print("Created an empty persistence file")
            #else:
            #    if self.DEBUG:
            #        print("Persistence file existed. Will try to save to it.")


            with open(self.persistence_file_path) as f:
                if self.DEBUG:
                    print("saving persistent data: " + str(self.persistent_data))
                json.dump( self.persistent_data, open( self.persistence_file_path, 'w+' ) )
                return True

        except Exception as ex:
            print("Error: could not store data in persistent store: " + str(ex) )
            return False


    
    
    
    
def get_int_or_float(v):
    number_as_float = float(v)
    number_as_int = int(number_as_float)
    if number_as_float == number_as_int:
        return number_as_int
    else:
        return float( int( number_as_float * 1000) / 1000)
        
        
        



#
#  ADAPTER
#        
        
class HighlightsAdapter(Adapter):
    """Adapter that can hold and manage things"""

    def __init__(self, api_handler, verbose=False):
        """
        Initialize the object.

        verbose -- whether or not to enable verbose logging
        """

        self.api_handler = api_handler
        self.name = self.api_handler.addon_name #self.__class__.__name__
        #print("adapter name = " + self.name)
        self.adapter_name = self.api_handler.addon_name #'Highlights-adapter'
        Adapter.__init__(self, self.adapter_name, self.adapter_name, verbose=verbose)
        self.DEBUG = self.api_handler.DEBUG
        


    def remove_thing(self, device_id):
        if self.DEBUG:
            print("Removing highlight thing: " + str(device_id))
        
        try:
            self.api_handler.delete_thing(device_id)
            obj = self.get_device(device_id)
            self.handle_device_removed(obj)                     # Remove from device dictionary

        except Exception as ex:
            print("Could not remove thing from highligh adapter devices: " + str(ex))
        

#
#  DEVICE
#

class HighlightsDevice(Device):
    """Highlight device type."""

    def __init__(self, handler, adapter, device_name, device_title, device_type):
        """
        Initialize the object.
        adapter -- the Adapter managing this device
        """

        
        Device.__init__(self, adapter, device_name)
        #print("Creating Highlight thing")
        
        self._id = device_name
        self.id = device_name
        self.adapter = adapter
        self.handler = handler
        self._type.append(device_type)

        self.name = device_name
        self.title = device_title
        self.description = 'Highlight device'

        #if self.adapter.DEBUG:
        #print("Empty Highlight thing has been created. device_name = " + str(self.name))
        #print("new thing's adapter = " + str(self.adapter))




#
#  PROPERTY
#


class HighlightsProperty(Property):
    """Highlight property type."""

    def __init__(self, device, name, description, value, original_thing_id, original_property_id):
        Property.__init__(self, device, name, description)
        
        self.original_thing_id = original_thing_id
        self.original_property_id = original_property_id
        self.device = device
        self.name = name
        self.title = name
        self.description = description # dictionary
        self.value = value
        self.set_cached_value(value)
        self.device.notify_property_changed(self)



    def set_value(self, value):
        #print("set_value is called on a Highlight property.")
        
        #todo: call the API here using the provided endpoint, in order to sync the values.
        try:
            data_to_put = { str(self.original_property_id) : value }
            #print("data_to_put = " + str(data_to_put))
            api_put_result = self.device.handler.api_put( '/things/' + str(self.original_thing_id) + '/properties/' + str(self.original_property_id), data_to_put )
            #print("api_put_result = " + str(api_put_result))
        except Exception as ex:
            print("property:set value:error: " + str(ex))
        #pass


    def update(self, value):
        #print("highlight property -> update to: " + str(value))
        #print("--prop details: " + str(self.title) + " - " + str(self.original_property_id))
        #print("--pro device: " + str(self.device))
        if value != self.value:
            self.value = value
            self.set_cached_value(value)
            self.device.notify_property_changed(self)
        
        