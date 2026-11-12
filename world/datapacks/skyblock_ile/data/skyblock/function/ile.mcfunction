# Génère l'île de départ une seule fois
forceload add -16 -16 16 16
# Île en L : 6x6 sur 3 couches, avec un coin retiré
fill -1 62 -1 4 63 4 minecraft:dirt
fill -1 64 -1 4 64 4 minecraft:grass_block
fill 2 62 2 4 64 4 minecraft:air
setblock 0 61 0 minecraft:bedrock
# Arbre
setblock 3 64 0 minecraft:dirt
place feature minecraft:oak 3 65 0
# Coffre de départ
setblock 0 65 4 minecraft:chest[facing=north]{Items:[{Slot:0b,id:"minecraft:lava_bucket",count:1},{Slot:1b,id:"minecraft:ice",count:2},{Slot:2b,id:"minecraft:bone_meal",count:8},{Slot:3b,id:"minecraft:melon_seeds",count:1},{Slot:4b,id:"minecraft:pumpkin_seeds",count:1},{Slot:5b,id:"minecraft:sugar_cane",count:1},{Slot:6b,id:"minecraft:cactus",count:1},{Slot:9b,id:"cobblemon:poke_ball",count:10},{Slot:10b,id:"cobblemon:oran_berry",count:4}]}
# Machine à fusion (modèle du resource pack) + barrières pour la collision
summon minecraft:item_display 0.0 65.5 1.5 {Tags:["machine_fusion"],item_display:"none",brightness:{sky:15,block:15},item:{id:"minecraft:paper",count:1,components:{"minecraft:custom_model_data":7001}}}
fill -1 65 1 0 66 1 minecraft:barrier
# Point d'apparition
setworldspawn 1 65 -1
gamerule spawnRadius 0
gamerule doInsomnia false
forceload remove -16 -16 16 16
scoreboard players set #fait skyblock_init 1
tellraw @a {"text":"Île Skyblock générée !","color":"light_purple"}
