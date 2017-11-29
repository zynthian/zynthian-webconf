function connectZynthianWebSocket(onopenDeferred){
	var url = window.location.href
	var parts = url.split("/");
	var zynthianSocket = new WebSocket("ws://"+parts[2]+"/api/ws");
	zynthianSocket.onconnecting = function(evn){
		console.log("zynthianSocket:onconnecting:",evn);

	}
	zynthianSocket.onopen = function(evn){
		console.log("zynthianSocket:onopen:",evn);
		this.messageHandler = {};
		onopenDeferred.resolve();
	}
	zynthianSocket.onclose = function(evn){
		console.log("zynthianSocket.onclose:",evn);
	}

	zynthianSocket.onmessage = function(evn){
		console.log("zynthianSocket.onmessage:",evn.data);
		var jsonMessage = JSON.parse(evn.data);
		if (this.messageHandler[jsonMessage._handler_name]){
			this.messageHandler[jsonMessage._handler_name](jsonMessage._data);
		}
	}


	zynthianSocket.registerHandler = function(handlerName, onmessage) {
		this.messageHandler[handlerName] = onmessage;
	}
	window.zynthianSocket = zynthianSocket;
}
