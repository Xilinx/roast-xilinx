set yaml_output_path [lindex $argv 0]
set filename "$yaml_output_path"
set output [ ::hsi::utils::get_all_app_details -json ]
# open the filename for writing
set fileId [open $filename "w"]
puts -nonewline $fileId $output
close $fileId
