// /** @odoo-module **/
import { patch } from "@web/core/utils/patch";
// import { MapRenderer } from "@web_map/static/src/map_view/map_renderer";


import {MapRenderer} from "../../../../web_map/static/src/map_view/map_renderer"

patch(MapRenderer.prototype, {
    get apiTilesRoute() {
        // Array of subdomains
        const subdomains = ['mt0', 'mt1', 'mt2', 'mt3'];
        
        // Randomly select a subdomain
        const subdomain = subdomains[Math.floor(Math.random() * subdomains.length)];
        
        // Return the custom tile URL with the selected subdomain
        return `https://${subdomain}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}`;
    }
});

patch(MapRenderer.prototype, {
    async addRoutes() {

        super.addRoutes();
        
        this.removeRoutes(); // Clear any existing routes
    
        // Check if there are enough markers to create a route
        if (this.markers.length < 2) {
            console.warn("Not enough markers to create a route.");
            return;
        }
    
        // Collect marker coordinates
        const coordinates = this.markers.map(marker => marker.getLatLng());
    
        // Construct the OSRM API URL
        const osrmBaseUrl = "https://router.project-osrm.org/route/v1/driving/";
        const coordsString = coordinates.map(coord => `${coord.lng},${coord.lat}`).join(";");
        const url = `${osrmBaseUrl}${coordsString}?geometries=geojson&overview=full`;
    
        // Fetch the route from the OSRM API
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`OSRM API error: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.routes || data.routes.length === 0) {
                    console.warn("No route found.");
                    return;
                }
    
                // Extract the route geometry
                const routeCoordinates = data.routes[0].geometry.coordinates.map(coord => [coord[1], coord[0]]);
    
                // Create a polyline from the route geometry
                const polyline = L.polyline(routeCoordinates, {
                    color: "blue", // Customize the route color
                    weight: 5,     // Line thickness
                    opacity: 0.8   // Line opacity
                }).addTo(this.leafletMap);
    
                // Save the polyline for later reference or cleanup
                this.polylines.push(polyline);
    
                // Fit the map to the route bounds
                this.leafletMap.fitBounds(polyline.getBounds());
            })
            .catch(error => {
                console.error("Failed to fetch route from OSRM:", error);
            });

    }
});


