/*eslint-env es6*/
/*global document*/
const UK_COLOUR='#0000ff'


if(sessionStorage.getItem('shown_about')!='shown'){
	console.log('about');
	$("#about_popup").fadeIn();
	sessionStorage.setItem('shown_about','shown');
}




class Country {
    constructor(name,code,border_status,colour,id=null,url=null) {
        this.id=id;
        this.name=name;
        this.border_status=border_status;
        this.colour=colour;
        this.code=code;
        this.url=url;
        this.element=document.getElementById(this.code);

        let i=0;
        let elements=[this.element];
        while(i<elements.length){
        	if(elements[i].tagName=='g'){
        		elements.push(... elements[i].children)
        	}else{
        		elements[i].style.fill=this.colour;
        		elements[i].style.cursor="pointer";
        	}
        	i++;
        };

        let self=this;
    	this.element.addEventListener("mouseenter",function(){
        	if(self.border_status==0){
        		document.getElementById('country_name').innerHTML=self.name+' n/a';
        		document.getElementById('country_name').style.backgroundColor=UK_COLOUR;
        	}else{
        		document.getElementById('country_name').innerHTML=self.name+' '+self.border_status;
        		document.getElementById('country_name').style.backgroundColor=self.colour;
        	}
        });
    	if(this.id){
	    	this.element.addEventListener("click",function(event){
	    		document.getElementById('popup').scrollTop=0;
	    		document.getElementById('popup_summary').innerHTML='';
	    		if(event.clientX/$(document).width()<0.5){
	    			document.getElementById('popup').style.left="49\%";
	    		}else{
	    			document.getElementById('popup').style.left="1\%";
	    		}
	    		document.getElementById('popup').style.display='inline-block';
	            if(self.border_status==0){
	            	document.getElementById('popup_bar_country_name').innerHTML=self.name;
	        		document.getElementById('popup_bar_country_name').style.backgroundColor='';
	        	}else{
	        		document.getElementById('popup_bar_country_name').innerHTML=self.name+' '+self.border_status;
	        		document.getElementById('popup_bar_country_name').style.backgroundColor=self.colour;
	        	}
	            document.getElementById('popup_fco_link').href=self.url;
	            document.getElementById('popup_country_name').innerHTML=self.name;
	            $.ajax({
	                url:get_summary_url,
	                type:'get',
	                data:{id:self.id},
	                success:function(data){
	                    document.getElementById('popup_summary').innerHTML=data}
	            })
	            event.stopPropagation();
	    	});
    	}
    }
}



new Country("United Kingdom",'gb',0,UK_COLOUR)
new Country("Isle of Man",'im',0,UK_COLOUR)
new Country("Jersey",'je',0,UK_COLOUR)
new Country("Guernsey",'gg',0,UK_COLOUR)


document.getElementById('close_popup_button').addEventListener("click",function(){
	document.getElementById('popup').style.display='none';
});

document.getElementById('close_about_button').addEventListener("click",function(){
	document.getElementById('about_popup').style.display='none';
	localStorage.setItem('shown_about','shown');
});

document.getElementById('about_button').addEventListener("click",function(){
	document.getElementById('about_popup').style.display='inline-block';
});

document.getElementById('ocean').addEventListener("click",function(){
	document.getElementById('popup').style.display='none';
});

