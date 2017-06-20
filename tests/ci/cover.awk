BEGIN{
    template = "%6s   %-75s\n"
    printf template, "Delta", "Module Path"
}

/^-/{
    s = substr($1, 2)
    x[s] = $3;
};

/^+/{
    s = substr($1, 2)
    d = $3
    if (s in x)
       d = d - x[s]
    y[s" "d] = d
}

END{
    asorti(y, z1, "@val_num_asc")
    for (i=1; i <= length(z1); i++){
        split(z1[i], z2, " ")
        printf template, z2[2], z2[1]
    }
}
