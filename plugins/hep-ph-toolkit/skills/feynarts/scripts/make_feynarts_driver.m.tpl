SetDirectory["{feynarts_state_dir}"];
AppendTo[$Path, "{sarah_path}/.."];
Needs["SARAH`"];
Start["{model_name}"];
MakeFeynArts[];
Exit[0];
