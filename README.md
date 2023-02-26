
# JsonMap2Obj

Blender script to reconstruct a map mesh from it's list of blocks

 This script requires data from three external other tools:

## Map block exporter

The [map block exporter plugin](https://github.com/tm-dojo/map-blocks-exporter) is an [Openplanet](https://openplanet.dev/) plugin which outputs a json object containing all the block informations for a given map.

Here is what the array looks like:

```json
{
	"nadeoBlocks": [
		{
			"name": "RoadTechDiagRightStartCurve1In",
			"pos": [ 784, 12, 848 ],
			"dir": 0,
			"blockOffsets": [
				[ 0, 0, 0 ],
				[ 1, 0, 0 ],
				[ 1, 0, 1 ],
				[ 0, 0, 1 ]
			]
		},
		{...}
	],
	"freeModeBlocks": [ ],
	"anchoredObjects": [ ]
}
```

## Nadeo block Item GBX scrapper

The [Nadeo block item exporter](https://github.com/RuurdBijlsma/tm-convert-blocks-to-items) is an [Openplanet](https://openplanet.dev/) plugin which scraps all available Nadeo blocks ingame and exports it as .Item.Gbx files (required to then extract the 3D mesh for those blocks)

## Gbx2Obj

[Gbx2Obj](https://github.com/tm-dojo/Gbx2Obj) is a .net program that goes through the exported .Item.Gbx blocks and converts it in 3D .obj mesh

## How to use

This blender script will ask you to enter the absolute path of the map json file (generated with the [map block exporter plugin](https://github.com/tm-dojo/map-blocks-exporter)) 

Once all the block informations about the map is loaded, it will then ask you to give the root folder where all the Block 3D mesh are located.

It will then go through all the blocks, and place it on the scene.