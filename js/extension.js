(function() {
  class Highlights extends window.Extension {
    constructor() {
      	super('highlights');
		//console.log("Adding highlights addon to menu");
      	this.addMenuEntry('Highlights');

      	this.content = '';
		
		this.item_elements = ['thing1','property1'];
		this.all_things;
		this.items_list = [];
		
		this.item_number = 0;

		fetch(`/extensions/${this.id}/views/content.html`)
        .then((res) => res.text())
        .then((text) => {
         	this.content = text;
        })
        .catch((e) => console.error('Failed to fetch content:', e));
    }



    show() {
		this.view.innerHTML = this.content;
	  	//console.log("highlights show called");

		const pre = document.getElementById('extension-highlights-response-data');
		//const original = document.getElementById('extension-highlights-original-item');
		//const list = document.getElementById('extension-highlights-list');
		
		const leader_dropdown = document.querySelectorAll(' #extension-highlights-view #extension-highlights-original-item .extension-highlights-thing1')[0];
		const highlight_dropdown = document.querySelectorAll(' #extension-highlights-view #extension-highlights-original-item .extension-highlights-thing2')[0];
	
		pre.innerText = "";
		
	  	// Click event for ADD button
		document.getElementById("extension-highlights-add-button").addEventListener('click', () => {
			this.items_list.push({'enabled': false});
			this.regenerate_items(this.items_list);
	  	});
		

		// Pre populating the original item that will be clones to create new ones
	    API.getThings().then((things) => {
			
			this.all_things = things;
			//console.log("all things: ");
			//console.log(things);
			
			// pre-populate the hidden 'new' item with all the thing names
			var thing_ids = [];
			var thing_titles = [];
			
			for (let key in things){
				try{
					
					var thing_title = 'unknown';
					if( things[key].hasOwnProperty('title') ){
						thing_title = things[key]['title'];
					}
					else if( things[key].hasOwnProperty('label') ){
						thing_title = things[key]['label'];
					}
					
					//console.log("thing_title = " + thing_title);
					/*
					try{
						if (thing_title.startsWith('highlights-') ){
							// Skip items that are already highlight clones themselves.
							//console.log(thing_title + " starts with highlight-, so skipping.");
							continue;
						}
						
					}
					catch(e){console.log("error in creating list of things for highlights: " + e);}
					*/
					
					var thing_id = things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1);
					//console.log("thing_id = " + thing_id);
					
					try{
						if (thing_id.startsWith('highlights-') ){
							// Skip items that are already highlight clones themselves.
							//console.log(thing_title + " starts with highlight-, so skipping.");
							continue;
						}
						
					}
					catch(e){console.log("error in creating list of things for highlights: " + e);}
				
					thing_ids.push( things[key]['href'].substr(things[key]['href'].lastIndexOf('/') + 1) );
				
				
					// for each thing, get its property list. Only add it to the selectable list if it has properties that are numbers. 
					// In case of the second thing, also make sure there is at least one non-read-only property.
					const property_lists = this.get_property_lists(things[key]['properties']);
				
					if(property_lists['property1_list'].length > 0){
						//console.log("adding thing to source list because a property has a number");
						leader_dropdown.options[leader_dropdown.options.length] = new Option(thing_title, thing_id);
					}
				}
				catch(e){console.log("error in creating list of things for highlights: " + e);}
			}
			
	  		// Get list of items
	        window.API.postJson(
	          `/extensions/${this.id}/api/init`

	        ).then((body) => {
				console.log("Python API result:");
				console.log(body);
				//console.log(body['items']);
				if(body['state'] == 'ok'){
					this.items_list = body['items'];
					this.regenerate_items(body['items']);
				}
				else{
					console.log("not ok response while getting items list");
					pre.innerText = body['state'];
				}
				

	        }).catch((e) => {
	          	//pre.innerText = e.toString();
	  			//console.log("highlights: error in calling init via API handler");
	  			console.log(e.toString());
				pre.innerText = "Loading items failed - connection error";
	        });				
				
	    });		

	}
	
	
	
	//
	//  REGENERATE ITEMS
	//
	
	regenerate_items(items){
		//console.log("regenerating");
		//console.log("this.all_things = ");
		//console.log(this.all_things);
		
		//const leader_property_dropdown = document.querySelectorAll(' #extension-highlights-view #extension-highlights-original-item .extension-highlights-property2')[0];
		//const highlight_property_dropdown = document.querySelectorAll(' #extension-highlights-view #extension-highlights-original-item .extension-highlights-property2')[0];
		
		try {
		
			const original = document.getElementById('extension-highlights-original-item');
			const list = document.getElementById('extension-highlights-list');
			list.innerHTML = "";
		
			// Loop over all items
			for( var item in items ){
				var clone = original.cloneNode(true);
				clone.removeAttribute('id');

				// Add delete button click event
				const delete_button = clone.querySelectorAll('.extension-highlights-item-delete-button')[0];
				delete_button.addEventListener('click', (event) => {
					var target = event.currentTarget;
					var parent3 = target.parentElement.parentElement.parentElement; //parent of "target"
					parent3.classList.add("delete");
			  });
			
				const final_delete_button = clone.querySelectorAll('.rule-delete-confirm-button')[0];
				final_delete_button.addEventListener('click', (event) => {
					var target = event.currentTarget;
					var parent3 = target.parentElement.parentElement.parentElement; //parent of "target"
					var parent4 = parent3.parentElement;
					parent4.removeChild(parent3);
					parent4.dispatchEvent( new CustomEvent('change',{bubbles:true}) );
				});
			
				const cancel_delete_button = clone.querySelectorAll('.rule-delete-cancel-button')[0];
				cancel_delete_button.addEventListener('click', (event) => {
					var target = event.currentTarget;
					var parent3 = target.parentElement.parentElement.parentElement;
					parent3.classList.remove("delete");
				});
				
				// Change switch icon
				clone.querySelectorAll('.switch-checkbox')[0].id = 'toggle' + this.item_number;
				clone.querySelectorAll('.switch-slider')[0].htmlFor = 'toggle' + this.item_number;
				this.item_number++;
				
				
			
				// Populate the properties dropdown
				try{
					for( var thing in this.all_things ){
						
						//console.log("this.all_things[thing]['id'] = " + this.all_things[thing]['id']);
						//console.log("items[item]['thing1'] = " + items[item]['thing1']);
						
						if( this.all_things[thing]['id'].endsWith( items[item]['thing1'] ) ){
							//console.log("bingo, at thing1. Now to grab properties:");
							//console.log(this.all_things[thing]);
							//console.log(this.all_things[thing]['properties']);
							const property1_dropdown = clone.querySelectorAll('.extension-highlights-property1')[0];
							const property_lists = this.get_property_lists(this.all_things[thing]['properties']);
							//console.log("property lists:");
							//console.log(property_lists);
							
							for( var title in property_lists['property1_list'] ){
								//console.log("adding prop title:" + property_lists['property1_list'][title]);
								property1_dropdown.options[property1_dropdown.options.length] = new Option(property_lists['property1_list'][title], property_lists['property1_system_list'][title]);
							}
						}
					}
				}
				catch (e) {
					console.log("Could not loop over all_things: " + e); // pass exception object to error handler
				}
				
			
				// Update to the actual values of regenerated item
				for(var key in this.item_elements){
					try {
						if(this.item_elements[key] != 'enabled'){
							clone.querySelectorAll('.extension-highlights-' + this.item_elements[key] )[0].value = items[item][ this.item_elements[key] ];
						}
					}
					catch (e) {
						//console.log("Could not regenerate actual values of highlight: " + e);
					}
				}
				
				// Set enabled state of regenerated item
				if(items[item]['enabled'] == true){
					//clone.querySelectorAll('.extension-highlights-enabled')[0].removeAttribute('checked');
					clone.querySelectorAll('.extension-highlights-enabled' )[0].checked = items[item]['enabled'];
				}
				list.append(clone);
			}
			
			

			//
			//  Change listener. Called if the user changes anything in the existing items in the list. Mainly used to update properties if a new thing is selected.
			//
			
			list.addEventListener('change', (event) => {
				//console.log("changed");
				//console.log(event);
				
				try {
					
					// Loops over all the things, and when a thing matches the changed element, its properties list is updated.
					for( var thing in this.all_things ){
						//console.log( this.all_things[thing] );
						
						if( this.all_things[thing]['id'].endsWith( event['target'].value ) ){
							const property_dropdown = event['target'].nextSibling;
							const property_lists = this.get_property_lists(this.all_things[thing]['properties']);
							try{
								var select_length = property_dropdown.options.length;
								for (var i = select_length-1; i >= 0; i--) {
									property_dropdown.options[i] = null;
								}
							}
							catch(e){
								console.log("error clearing property dropdown select options: " + e);
							}
							
							// If thing1 dropdown was changed, update its property titles
							if( event['target'].classList.contains("extension-highlights-thing1") ){
								//console.log("changed thing1 dropdown");
								for( var title in property_lists['property1_list'] ){
									property_dropdown.options[property_dropdown.options.length] = new Option(property_lists['property1_list'][title], property_lists['property1_system_list'][title]);
								}
								
								// If the thing selector is changed, always disable the item.
								var item_element = event['target'].parentElement.parentElement.parentElement.parentElement;
								item_element.querySelectorAll('.extension-highlights-enabled')[0].checked = false;
							}
						}
					}
					
				}
				catch (e) {
					console.log("error handling change in highlight: " + e);
				}
				
				var updated_values = [];
				const item_list = document.querySelectorAll('#extension-highlights-list .extension-highlights-item');
				
				// Loop over all the elements
				item_list.forEach(item => {
					var new_values = {};
					var incomplete = false;
					
					// For each item in the highlights list, loop over all values in the item to check if they are filled.
					for (let value_name in this.item_elements){
						try{
							const new_value = item.querySelectorAll('.extension-highlights-' + this.item_elements[value_name])[0].value;
							console.log("new_value = " + new_value);
							console.log("new_value.length = " + new_value.length);
							if(new_value.length > 0){
								new_values[ this.item_elements[value_name] ] = item.querySelectorAll('.extension-highlights-' + this.item_elements[value_name])[0].value;
							}
							else{
								incomplete = true;
							}
						}
						catch(e){console.log("Error checking all values of item: " + e);}
					}
					//item.classList.remove('new');
					// Check if this item is enabled
					new_values['enabled'] = item.querySelectorAll('.extension-highlights-enabled')[0].checked;
					
					updated_values.push(new_values);
					
				});
				
				//console.log("updated_values:");
				//console.log(updated_values);
				
				
				// Send new values to backend
				
				window.API.postJson(
					`/extensions/${this.id}/api/update_items`,
					{'items':updated_values}
				).then((body) => { 
					//thing_list.innerText = body['state'];
					//console.log(body); 
					if( body['state'] != 'ok' ){
						pre.innerText = body['state'];
					}

				}).catch((e) => {
					console.log("highlights: error in save items handler");
					pre.innerText = e.toString();
				});
				
			});
			
		}
		catch (e) {
			// statements to handle any exceptions
			console.log(e); // pass exception object to error handler
		}
	}
	




	//
	//  A helper method that generates nice lists of properties from a Gateway property dictionary
	//
	get_property_lists(properties){
		//console.log("checking properties on:");
		//console.log(properties);
		var property1_list = []; // list of user friendly titles
		var property1_system_list = []; // list internal property id's
		
		for (let prop in properties){
			//console.log(properties[prop]);
			var title = 'unknown';
			if( properties[prop].hasOwnProperty('title') ){
				title = properties[prop]['title'];
			}
			else if( properties[prop].hasOwnProperty('label') ){
				title = properties[prop]['label'];
			}
				
			
			var system_title = properties[prop]['links'][0]['href'].substr(properties[prop]['links'][0]['href'].lastIndexOf('/') + 1);

			// If a property is a number, add it to the list of possible source properties
			if( properties[prop]['type'] == 'integer' || properties[prop]['type'] == 'float' || properties[prop]['type'] == 'number' || properties[prop]['type'] == 'boolean'){
				
				property1_list.push(title);
				property1_system_list.push(system_title);

			}
		}
		
		
		return { 'property1_list' : property1_list, 'property1_system_list' : property1_system_list };
	}

		
		
		
		
	// HELPER METHODS
	
	hasClass(ele,cls) {
		//console.log(ele);
		//console.log(cls);
	  	return !!ele.className.match(new RegExp('(\\s|^)'+cls+'(\\s|$)'));
	}

	addClass(ele,cls) {
	  	if (!this.hasClass(ele,cls)) ele.className += " "+cls;
	}

	removeClass(ele,cls) {
	  	if (this.hasClass(ele,cls)) {
	    	var reg = new RegExp('(\\s|^)'+cls+'(\\s|$)');
	    	ele.className=ele.className.replace(reg,' ');
	  	}
	}
		
		

  }

  new Highlights();
	
})();


