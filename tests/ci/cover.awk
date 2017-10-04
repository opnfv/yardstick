BEGIN{
    total = 0
    increase_total = 0
    decrease_total = 0
    template = "%6s   %-75s\n"
    printf template, "Delta", "Module Path"
}

function process_sub(file_path, line_count){
    if ((file_path == "--") || (file_path == "TOTAL"))
        return
    line_count *= -1
    decrease[file_path] = line_count
    delta_list[file_path" "line_count] = line_count
}

/^-/{
    process_sub(substr($1, 2), $3)
};

function process_add(file_path, line_count){
    if ((file_path == "++") || (file_path == "TOTAL"))
        return
    if (file_path in decrease){
        previous_count = decrease[file_path]
        line_count += previous_count
        delete delta_list[file_path" "previous_count]
    }
    delta_list[file_path" "line_count] = line_count
}

/^+/{
    process_add(substr($1, 2), $3)
}

END{
    asorti(delta_list, sorted_delta_list, "@val_num_asc")
    for (idx=1; idx <= length(sorted_delta_list); idx++){
        split(sorted_delta_list[idx], split_sorted_delta_list, " ")
        file_path = split_sorted_delta_list[1]
        line_count = split_sorted_delta_list[2]
        printf template, line_count, file_path
        total += line_count
        if (line_count > 0)
            increase_total += line_count
        else
            decrease_total += line_count
    }
    printf template, "----", "----"
    printf template, total, "Total"
    printf template, increase_total, "Increase Total"
    printf template, decrease_total, "Decrease Total"
}
