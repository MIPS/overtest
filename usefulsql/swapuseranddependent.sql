UPDATE ovt_dependency
SET versionedactionid=versionedactiondep, versionedactiondep=versionedactionid
FROM
(SELECT DISTINCT dependencyid
  FROM 
  ((SELECT ovt_dependency.dependencyid
    FROM ovt_action INNER JOIN ovt_actioncategory USING (actioncategoryid)
         INNER JOIN ovt_versionedaction USING (actionid)
         INNER JOIN ovt_dependency USING (versionedactionid)
    WHERE ovt_actioncategory.actioncategoryname='<NAME>')
   UNION
   (SELECT ovt_dependency.dependencyid
    FROM ovt_action INNER JOIN ovt_actioncategory USING (actioncategoryid)
         INNER JOIN ovt_versionedaction USING (actionid)
         INNER JOIN ovt_dependency ON (ovt_versionedaction.versionedactionid=ovt_dependency.versionedactiondep)
    WHERE ovt_actioncategory.actioncategoryname='<NAME>')) AS a) AS b
   WHERE b.dependencyid=ovt_dependency.dependencyid

