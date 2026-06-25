# Attachables

Put files in this `attachables/` folder, then describe each file below.

The bot can send an attachment when the buyer asks for something relevant, like a brochure,
floor plan, price sheet, payment plan, map, location details, or layout.

Required fields:
- `id`: short stable id used by the bot
- `file`: exact filename inside `attachables/`
- `type`: `document`, `image`, `video`, or `audio`
- `description`: what the file contains
- `keywords`: comma-separated phrases buyers might use

Optional fields:
- `caption`: caption sent with the WhatsApp attachment

Example entries are below. Replace filenames with your real files when you add them.

## Dummy Brochure
id: dummy-brochure
file: dummy-brochure.pdf
type: document
description: Dummy Sector Zero brochure placeholder. Send this when the customer asks for more details, project details, a brochure, amenities, overview, or general information about Sector Zero.
keywords: more details, details, project details, send details, brochure, project brochure, more information, info, information, amenities, sector zero, overview
caption: Sharing the Sector Zero brochure details.

## Floor Plans
id: floor-plans
file: floor-plans.pdf
type: document
description: Floor plans and layouts for 1 BHK, 2 BHK, and 3 BHK configurations.
keywords: floor plan, layout, plan, 1 bhk, 2 bhk, 3 bhk, carpet area
caption: Sharing the floor plans.

## Location Map
id: location-map
file: location-map.jpg
type: image
description: Location map for Sector Zero in Airoli, Navi Mumbai with nearby landmarks and connectivity.
keywords: map, location, address, where, nearby, connectivity, airoli, directions
caption: Sharing the location map.

