COPY(SELECT resource.name,
    CONCAT('https://www.gis-hub.ca/dataset/', package.name) AS url,
    package.title, package.maintainer_email,
    initcap(split_part(split_part(package.maintainer_email, '.', 1), '@', 1)) AS maintainer_name,
    DATE_PART('day', NOW() - resource.last_modified::timestamp) AS days_since_modified,
    package_extra.value AS update_frequency
FROM public.resource
JOIN public.package ON public.resource.package_id=public.package.id
JOIN public.package_extra ON public.package.id=public.package_extra.package_id
WHERE package.state='active' AND resource.state='active' AND package_extra.key='update_frequency'
ORDER BY days_since_modified DESC)
TO '/tmp/maintainer_details.csv'
WITH CSV HEADER DELIMITER ',';