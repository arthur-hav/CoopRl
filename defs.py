robot = {
"health":110, "energy":100,
"mr":3, "armor":3,
"ad":18, "attack_range":1,
"jclass":"robot" }

zombie = {
"health":60, "energy":100,
"mr":2, "armor":2,
"ad":3, "attack_range":1,
"jclass":"zombie" }

archer_skeleton = {
"health":30, "energy":100,
"mr":0, "armor":2,
"ad":2, "attack_range":4,
"jclass":"skeleton" }

knife = {
"slot":"weapon"
}

waves = {
   6:{(0,-15): zombie,
       (-15, -7.5):zombie,
       (15, -7.5):zombie
       },
   120:{(0,-15): zombie,
       (-15, -7.5):archer_skeleton,
       (15, -7.5):archer_skeleton
       },
   240:{(0,-15): zombie,
       (-15, -7.5):zombie,
       (-15, -7.5):zombie,
       (15, -6.5):zombie,
       (15, -6.5):zombie
       }
}
