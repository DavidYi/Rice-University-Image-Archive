function addImage(baseUrl){
	console.log('hi');
	var map = L.map('map', {
                center: [0, 0],
                crs: L.CRS.Simple,
                zoom: 0,
        });

	var iiifLayer = L.tileLayer.iiif(baseUrl + '/info.json').addTo(map);

	var areaSelect = L.areaSelect({}).addTo(map);

	areaSelect.addTo(map);

	areaSelect.on('change', function() {
		var bounds = this.getBounds();
		var zoom = map.getZoom();
		var min = map.project(bounds.getSouthWest(), zoom);
		var max = map.project(bounds.getNorthEast(), zoom);
		var imageSize = iiifLayer._imageSizes[zoom];
		var xRatio = iiifLayer.x / imageSize.x;
		var yRatio = iiifLayer.y / imageSize.y;

		var x1 = Math.floor(min.x * xRatio);
		var y1 = Math.floor(max.y * yRatio);
		var x2 = Math.floor((max.x - min.x) * xRatio);
		var y2 = Math.floor((min.y - max.y) * yRatio);

		x1 = (x1 >= 0) ? x1 : 0;
		y1 = (y1 >= 0) ? y1 : 0;

		var region = [
			x1,
			y1,
			x2,
			y2
		];

		var coordinates = '/' + region.join(',');
		$('#cropForm input[name="coor"]').val(coordinates);
	});
	

	iiifLayer.on('load', function() {
		var maxNativeZoom = iiifLayer.maxNativeZoom;
		var b = [0, 0, 0, 0];
		var minPoint = L.point(b[0], b[1]);
		var maxPoint = L.point(parseInt(b[0]) + parseInt(b[2]), parseInt(b[1]) + parseInt(b[3]));

		var min = map.unproject(minPoint, maxNativeZoom);
		var max = map.unproject(maxPoint, maxNativeZoom);

		var y = max.lat - min.lat
		var x = max.lng - min.lng

		// Pop a rectangle on there to show where it goes
		L.rectangle(L.latLngBounds(min, max)).addTo(map)
		var bounds = L.latLngBounds(min, max);
		map.panTo(bounds.getCenter())

		areaSelect.setDimensions({
			width: Math.round(Math.abs(x)),
			height: Math.round(Math.abs(y))
 		});
	});
}
