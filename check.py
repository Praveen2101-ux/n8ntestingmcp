<form version="1.1" hideFilters="false" script="multiselect_handler.js,table_header_tooltip_utils.js,input_tooltip.js,help_button.js,ruleset_button.js,app_version_info.js,disable_hyperlink_redirection_warning.js,clear_cache.js,db_height_fixed_and_precalculated.js,Prefill_TestedVersion.js,auto_hide_filter_exportbutton.js">
  <label>Quality Management am detail testing</label>
  <init>
    <set token="table_tooltip_tokens">crsid,SysRSid,SwRSid</set>
    <set token="CRS_done">Waiting</set>
    <set token="SYS_total_done">Waiting</set>
    <set token="SYSARC_Total_done">Waiting</set>
    <set token="SWREQ_done">Waiting</set>
    <set token="SWArc_done">Waiting</set>
    <eval token="token_domain_overview">if(isnotnull($sys_total_domain$) OR isnotnull($sys_arch_total_domain$) OR isnotnull($sw_total_domain$) OR isnotnull($swArc_total_domain$) ,"noop",null())</eval>
    <set token="background_color_token"></set>
    <set token="font_style"></set>
    <set token="load_done">false</set>
    <set token="workitemidcrs"></set>
    <set token="workitemidsys"></set>
    <set token="workitemidsw"></set>
    <unset token="form.export"></unset>
  </init>
  <search id="release_filter">
    <query>| inputlookup Prefill_TestedVersion.csv 
    | search Release="$release_Label$" 
    | table Tested_version, Release
    </query>
    <earliest>0</earliest>
    <latest>now</latest>
    <done>
      <set token="testedversion_prio">$result.Tested_version$</set>
      <set token="release_prio">$result.Release$</set>
    </done>
  </search>
  <search id="last_time">
    <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_STD_Quality_Dashboard_Requirements_Elicitation" OR source="Summary_STD_Quality_Dashboard_System_Requirements" OR source="Summary_STD_Quality_Dashboard_Software_Requirements" OR source="Summary_STD_Quality_Dashboard_Problem_Resolution_Management")
      | head 1 
      | eval exportTime = strftime(_time, "%d.%m.%Y - %H:%M %Z")
      | table exportTime
    </query>
    <earliest>0</earliest>
    <latest>now</latest>
    <done>
      <set token="exportlatest">$result.exportTime$</set>
    </done>
  </search>
  <search id="initialSearch">
    <query>
        | makeresults | eval aa= "$time$"
        | eval bb="$latestTime$"
      </query>
    <done>
      <set token="load_done">true</set>
      <eval token="background_color_token">if(isnull($background_color_token$) OR "false"==$load_done$,"#F2F4F5",if($time$ == $latestTime$,"#C2E59D","#FFC91D"))</eval>
      <eval token="font_style">if(isnull($font_style$) OR "false"==$load_done$,"normal",if($time$ == $latestTime$,"normal","italic"))</eval>
    </done>
  </search>
  <!-- Handle SW Arch Linkage Check -->
  <search id="validateArchCheck">
    <query>
      | makeresults 
      | eval swArchLinks = lower(`prj_getSwArchLinkTypes`).",".lower(`prj_getSwcArchLinkTypes`)
      | eval swArchfield = if(like(swArchLinks,"%trace%"), ", \"SW ARCH element linked (trace)\"", "")
      | eval swArchfield = if(like(swArchLinks,"%satisfy%"), swArchfield.", \"SW ARCH element linked (satisfy)\"", swArchfield)
      | eval swArchfield = if(like(swArchLinks,"%refine%"), swArchfield.", \"SW ARCH element linked (refine)\"", swArchfield) 
      </query>
    <done>
      <set token="swArchLinks">$result.swArchLinks$</set>
      <set token="swArchfield">$result.swArchfield$</set>
    </done>
  </search>
  <!-- Get Release Label-->
  <search id="getAdditionalInfo">
    <query>| makeresults 
      | eval ReleaseLabel = `std_getReleaseLabel`, ReleaseAttribute = `std_getReleaseAttribute` 
      | table ReleaseLabel,ReleaseAttribute
    </query>
    <finalized>
      <condition match="'job.resultCount' != 0">
        <set token="releaseLabel">$result.ReleaseLabel$</set>
        <set token="releaseAttribute">$result.ReleaseAttribute$</set>
      </condition>
    </finalized>
  </search>
  <search id="testedVersionChange">
    <query> 
    | makeresults 
    | eval testedVersionLabel = "$form.testedVersion$"
    | eval selectedIteration = if(testedVersionLabel=".*", "ExecutionDate", "IterationStartDate") 
    | eval latestExecution = if(testedVersionLabel=".*", "\(L\)", ".*")
    | eval attributeToBeConsidered = if(testedVersionLabel=".*", "RQM_TestArtifactsOrderedByExecution",  "RQM_TestArtifacts") 
    | table selectedIteration, latestExecution, attributeToBeConsidered
    </query>
    <done>
      <condition match="'job.resultCount' != 0">
        <set token="testedVersionDate">$result.selectedIteration$</set>
        <set token="latestExecution">$result.latestExecution$</set>
        <set token="attributeToBeConsidered">$result.attributeToBeConsidered$</set>
      </condition>
    </done>
  </search>
  <!-- Choose b/w 2 type base queries -->
  <search>
    <query>
| makeresults
| eval queryID = if($date_earliest$ &lt; `prj_getTCQueryChangeDate`, 1, 2)
| table queryID
    </query>
    <earliest>0</earliest>
    <latest>now</latest>
    <done>
      <condition match="$result.queryID$==1">
        <set token="queryID">1</set>
        <set token="query1">1</set>
        <unset token="query2"></unset>
      </condition>
      <condition>
        <set token="queryID">2</set>
        <unset token="query1"></unset>
        <set token="query2">2</set>
      </condition>
    </done>
  </search>
  <search>
    <query>
      | makeresults 
      | eval URL=`std_getGCURL` 
      | append 
          [ search (index=`std_getBaseIndex` OR index=`std_getMUIndex`)  source="*\\GC\\*" AND source="*GC_Context_*" 
          | table GC_Context, `std_getReleaseAttribute`, ReleaseNone] 
      | fillnull value="Not Defined" `std_getReleaseAttribute` 
      | fillnull value=1 ReleaseNone 
      | eval URL= if(isnull(GC_Context) OR trim(GC_Context)="", URL, GC_Context), 
          URL="\"".URL."\"" 
      | dedup URL sortby - GC_Context 
      | eval releaseCheck = if(((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) , 1, 0) 
      | table URL, `std_getReleaseAttribute`, ReleaseNone, GC_Context, releaseCheck 
      | sort - releaseCheck
    </query>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
    <done>
      <condition match="'job.resultCount' != 0">
        <set token="gcURL">$result.URL$</set>
      </condition>
      <condition>
        <eval token="gcURL">""</eval>
      </condition>
    </done>
  </search>
  <!--<search id="basesearchVer">
    <query>(index=`std_getBaseIndex` OR index=`std_getMUIndex`)  source=`DNG_All_ModuleCollection_mma_xc` AND source!=`DNG_Links_mma_xc` `DNG_10-PF_ALL_REQID_URL_Renaming_Table_mma_xc`
      | dedup Verification_Level
      | makemv Verification_Level delim="," 
      | mvexpand Verification_Level 
      | eval Verification_Level = trim(Verification_Level) 
      | dedup Verification_Level 
      | table Verification_Level
      | sort Verification_Level
    </query>
  </search>-->
  <search id="SysReqsearch" depends="$sys_total_domain$,$query1$">
    <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_System_Requirements" 
| where _time=max(_time) 
| fillnull value="" Contents
| fillnull value="Not Defined" `std_getReleaseAttribute`, SatisfiesRelease, SatisfiesLinkRelease, RQM_TestArtifacts, DesignLinkRelease, ProblemOrChangeReq, Team, Variant, SatisfiesVariant,`std_getStkhModule`
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked")
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule
| eval stRSProcessed = split(stkhModule,"; ")
| eval stRSReleaseFiltered = mvfilter((match(",".mvindex(split(stRSProcessed,"["),1).",","$release$") AND ".*"!="$release$") OR (".*"="$release$" AND match(",".mvindex(split(stRSProcessed,"["),1).",",",ReleaseNone,")) OR (" * "==" $stRSModule$ "))
| eval stRSFiltered = mvfilter(match(" ".stRSReleaseFiltered." "," $stRSModule$ "))
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) AND isnotnull(stRSFiltered)
| table DNGConfiguration_ID, DNGLocalConfigurationName, GCConfigurationID, DNGComponent_ID, 
    ModuleID, ModuleName, ModuleType, REQID, Contents, LinkStart_URL, ReqType, Domains, Status, Safety, Security, Legal, User_Function, Verification_Level, SW_Function, SW_Comp, SYS_Function, ReqDomain, ReqType, ProblemOrChangeReq, Team,
    PlannedFor, `std_getReleaseAttribute`, ReleaseNone, 
    SatisfiesURL, SatisfiesREQID, SatisfiesRelease, SatisfiesLinkRelease, SatisfiesLinkReleaseNone, 
    Design_Link_Type, DesignLinkRelease, DesignLinkReleaseNone,
    RQM_TestArtifacts, TC_Count, NoTestcase,
    Requirements_To_Be_Processed, Accepted_Requirements, 
    Requirements_Linked_To_Source, 
    Requirements_To_Be_Tested, Requirement_To_Be_Tested_Linked, Architectural_Element_Linked,Implement_details, Variant, SatisfiesVariant,Requirements_NotLinked_To_Source 
| makemv delim="||" RQM_TestArtifacts 
| mvexpand RQM_TestArtifacts 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,".,"),
    ValidatedByLinkRelease=mvindex(RQM_TestArtifacts,12),
    ValidatedByLinkReleaseNone=mvindex(RQM_TestArtifacts,13),
    TCERRelease=mvindex(RQM_TestArtifacts,14),
    TCERReleaseNone=mvindex(RQM_TestArtifacts,15),
    TRRelease=mvindex(RQM_TestArtifacts,17),
    TRReleaseNone=mvindex(RQM_TestArtifacts,18),
    TCRelease=mvindex(RQM_TestArtifacts,23),
    TCReleaseNone=mvindex(RQM_TestArtifacts,24),
    TC_Variant=mvindex(RQM_TestArtifacts,25)
| fillnull value="Not Defined" ValidatedByLinkRelease, TCERRelease, TRRelease, TCRelease 
| fillnull value=1 ValidatedByLinkReleaseNone, TCERReleaseNone, TRReleaseNone, TCReleaseNone 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND (match(",".TC_Variant.",", "$variant$")), 1, 0),
    TCERValidity = if((((match(",".TCERRelease.",","$release$") OR TCERRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCERReleaseNone=1)) , 1, 0) ,
    TRValidity = if((((match(",".TRRelease.",","$release$") OR TRRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TRReleaseNone=1)) AND LinkValidity = 1 , 1, 0) 
| eval ValidatedByLinkName=if(LinkValidity=1, mvindex(RQM_TestArtifacts,0), "Not Defined"),
    LinkEnd_URL=if(TCValidity=1, mvindex(RQM_TestArtifacts,1), "Not Defined"),
    TestCaseID=if(TCValidity=1, mvindex(RQM_TestArtifacts,2), "Not Defined"),
    TestCaseUUID=if(TCValidity=1, mvindex(RQM_TestArtifacts,3), "Not Defined"),
    TestCaseName=if(TCValidity=1, mvindex(RQM_TestArtifacts,4), "Not Defined"),
    TestSuiteID=if(TCValidity=1, mvindex(RQM_TestArtifacts,5), "Not Defined"),
    TestPlanID=if(TCValidity=1, mvindex(RQM_TestArtifacts,6), "Not Defined"),
    TCERID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,7), "Not Defined"),
    TCERWebID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,8), "Not Defined"),
    IterationID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,9), "Not Defined"),
    TCRID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,10), "Not Defined"),
    Verdict=if(TRValidity=1, mvindex(RQM_TestArtifacts,11), "Not Defined"),
    IterationStartDate=if(TCERValidity=1, mvindex(RQM_TestArtifacts,16), "0"),
    TCERCreationDate=if(isnull(mvindex(RQM_TestArtifacts,21)), IterationStartDate, mvindex(RQM_TestArtifacts,21)),
    ExecutionDate=if(isnull(mvindex(RQM_TestArtifacts,19)), IterationStartDate, if(TCERValidity=1, if(TRValidity=1, mvindex(RQM_TestArtifacts,19), TCERCreationDate), "0")), 
    LatestExecution=if(isnull(mvindex(RQM_TestArtifacts,20)), "(ND)", if(TRValidity=1, mvindex(RQM_TestArtifacts,20), "(ND)")),
    TCStatus=if(TCValidity=1, mvindex(RQM_TestArtifacts,22), "Others")
    `std_fillIterationID_Gaps` 
| eval testedInItr=if(((match(",".IterationID.",", "$testedVersion$")) AND TCERWebID!="Not Defined"),1,0) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,") 
| eval Type = mvindex(Implement_details,0),
       WorkitemID = mvindex(Implement_details,1),
       Summary = mvindex(Implement_details,2),
       FiledAgainst = mvindex(Implement_details,3),
       Iteration = mvindex(Implement_details,4),
       Tags = mvindex(Implement_details,5),
       "Issuer Class" = mvindex(Implement_details,6),
       "Status_Workitem" = mvindex(Implement_details,7),
       "Safety_Workitem" = mvindex(Implement_details,8),
       "Security_Workitem" = mvindex(Implement_details,9),
       "Legal_Workitem" = mvindex(Implement_details,10),
       CreationDate = mvindex(Implement_details,11),
       ClosureDate = mvindex(Implement_details,12) ,
       Implemented_URL = mvindex(Implement_details,13) 

| fillnull value="Others" TCStatus
| fillnull value="0" IterationStartDate, ExecutionDate 
| fillnull value="Not Defined" TestCaseID, TestPlanID, Verdict,`std_getReleaseAttribute`, SatisfiedByRelease, SatisfiesRelease 
| dedup ModuleID, REQID, LinkStart_URL, TestCaseID sortby -ReleaseNone,-LinkValidity, -TCValidity, -testedInItr, -$testedVersionDate$, -TCERValidity, -TCERWebID, -TRValidity, -TCRID 
| eval ReqTypeClassification = if((`prj_getSysRS`), "SYS", "DRS") 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval Valid_WorkitemID = if(WorkitemID!="Not Defined",WorkitemID, "Not Linked") 
| eventstats values(Valid_WorkitemID) delim=";" as linked_Implemented by ModuleID,LinkStart_URL, REQID,ReleaseNone
| eval Valid_TestCaseID = if(TestCaseID!="Not Defined",TestCaseID, null())
| eval Implemented_URL = if((NOT like(Implemented_URL,"%oslc_config%")) AND like(Implemented_URL, "https://rb-alm-__-p.de.bosch.com/ccm/%"), Implemented_URL.$gcURL$, Implemented_URL)
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0) 
| eventstats count(eval(ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval(Verdict="com.ibm.rqm.execution.common.state.passed" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval(Verdict="com.ibm.rqm.execution.common.state.error" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.blocked" OR Verdict="com.ibm.rqm.execution.common.state.paused" OR Verdict="com.ibm.rqm.execution.common.state.incomplete" OR Verdict="com.ibm.rqm.execution.common.state.inconclusive" OR Verdict="com.ibm.rqm.execution.common.state.partiallyblocked" OR Verdict="com.ibm.rqm.execution.common.state.deferred" OR Verdict="Not Defined" OR Verdict="com.ibm.rqm.execution.common.state.inprogress") AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted",
    values(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by ModuleID,LinkStart_URL, REQID 
| nomv Test_Case_Linked_temp 
    ``` 
| eval Test_Case_Linked_temp=Test_Case_Linked_temp.";" 
| rex field=Test_Case_Linked_temp max_match=0 "(?&lt;Test_Case_Linked&gt;(?: 
    [ \d]+;){1,10})"``` 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| eval 12_Total = if(like(ReqDomain,"$domain$"), Requirements_To_Be_Processed, 0),
    12_Actual = if(like(ReqDomain,"$domain$"), Requirements_Linked_To_Source, 0),
    11_Total = if("$domain$"="%%%", Requirements_To_Be_Processed, if(Requirements_To_Be_Processed&gt;0 AND ((like(Domains,"$domain$") AND "$domain$"!="%SYS%" AND ReqTypeClassification="DRS") OR ((like(Domains,"%Not Defined%") OR like(Domains,"%SYS%")) AND "$domain$"="%SYS%")), Requirements_To_Be_Processed, 0)),
    11_Actual = if("$domain$"="%%%", Accepted_Requirements, if(Accepted_Requirements&gt;0 AND ((like(Domains,"$domain$") AND "$domain$"!="%SYS%" AND ReqTypeClassification="DRS") OR ((like(Domains,"%Not Defined%") OR like(Domains,"%SYS%")) AND "$domain$"="%SYS%")), Accepted_Requirements, 0)),
    13_Total = if(like(ReqDomain,"$domain$"), Requirements_To_Be_Tested, 0),
    13_Actual = if(like(ReqDomain,"$domain$"), Requirement_To_Be_Tested_Linked, 0),
    3_Total = if(like(ReqDomain,"$domain$"), Requirements_To_Be_Tested, 0),
    3_Actual=if((Requirements_To_Be_Tested&gt;0 AND Verdict="PASSED" AND like(ReqDomain,"$domain$")), 1, 0) 
| eval LinkStart_URL = if((NOT like(LinkStart_URL,"%oslc_config%")) AND like(LinkStart_URL, "https://rb-alm-__-p.de.bosch.com/rm/%"), LinkStart_URL.$gcURL$, LinkStart_URL ),
    LinkEnd_URL = if((NOT like(LinkEnd_URL,"%oslc_config%")) AND like(LinkEnd_URL, "https://rb-alm-__-p.de.bosch.com/qm/%"), LinkEnd_URL.$gcURL$, LinkEnd_URL),
	12_Actual_old = '12_Actual',
    12_Actual = if(((match(",".SatisfiesRelease.",","$release$") AND (match(",".SatisfiesLinkRelease.",","$release$") OR SatisfiesLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND SatisfiesLinkReleaseNone=1)) AND (match(",".SatisfiesVariant.",", "$variant$")) , '12_Actual', 0) 
| eval 3_Pending = '3_Total' - '3_Actual',
    11_Pending = '11_Total' - '11_Actual',
    12_Pending = '12_Total' - '12_Actual',
    13_Pending = '13_Total' - '13_Actual' 
| where ('$form.selectedMetrics$'&gt;0) 
| eval metricID=mvindex(split("$form.selectedMetrics$","_"),0) 
| lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains  
    </query>
    <done>
      <set token="sysBasesid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <!-- SysRS TC query 2 -->
  <search id="SysReqsearch2" depends="$sys_total_domain$,$query2$">
    <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_System_Requirements" 
| where _time=max(_time) 
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, SatisfiesRelease, SatisfiesLinkRelease, RQM_TestArtifacts, DesignLinkRelease, ProblemOrChangeReq, Team, Variant, SatisfiesVariant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
| eval stRSReleaseFiltered = mvfilter((match(",".mvindex(split(stRSProcessed,"["),1).",","$release$") AND ".*"!="$release$") OR (".*"="$release$" AND match(",".mvindex(split(stRSProcessed,"["),1).",",",ReleaseNone,")) OR (" * "==" $stRSModule$ "))
| eval stRSFiltered = mvfilter(match(" ".stRSReleaseFiltered." "," $stRSModule$ ")) 
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) AND isnotnull(stRSFiltered) 
| table ModuleID, ModuleName, ModuleType, `std_getStkhModule`, REQID, Contents, LinkStart_URL, ReqType, Domains, Status, Safety, Security, Legal, User_Function, Verification_Level, SW_Function, SW_Comp, SYS_Function, ReqDomain, ProblemOrChangeReq, Team,
    PlannedFor, `std_getReleaseAttribute`, ReleaseNone, 
    SatisfiesURL, SatisfiesREQID, SatisfiesRelease, SatisfiesLinkRelease, SatisfiesLinkReleaseNone, 
    Design_Link_Type, DesignLinkRelease, DesignLinkReleaseNone,
    TC_Count, NoTestcase,
    Requirements_To_Be_Processed, Accepted_Requirements, 
    Requirements_Linked_To_Source, 
    Requirements_To_Be_Tested, Requirement_To_Be_Tested_Linked,"Architectural_Element_Linked",Implement_details, Variant, SatisfiesVariant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, 
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, TC_Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = $attributeToBeConsidered$ 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".TC_Variant.",", "$variant$") , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","$testedVersion$")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","$latestExecution$") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    TCERWebID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),1)),
    IterationID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "No Filter Match", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),2)),
    TCRID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),3)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4))
    `std_fillIterationID_Gaps` 
| eval testedInItr=if(((match(",".IterationID.",", "$testedVersion$")) AND TCERWebID!="Not Defined"),1,0) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,") 
| eval Type = mvindex(Implement_details,0),
    WorkitemID = mvindex(Implement_details,1),
    Summary = mvindex(Implement_details,2),
    FiledAgainst = mvindex(Implement_details,3),
    Iteration = mvindex(Implement_details,4),
    Tags = mvindex(Implement_details,5),
    "Issuer Class" = mvindex(Implement_details,6),
    "Status_Workitem" = mvindex(Implement_details,7),
    "Safety_Workitem" = mvindex(Implement_details,8),
    "Security_Workitem" = mvindex(Implement_details,9),
    "Legal_Workitem" = mvindex(Implement_details,10),
    CreationDate = mvindex(Implement_details,11),
    ClosureDate = mvindex(Implement_details,12) ,
    Implemented_URL = mvindex(Implement_details,13) 
| fillnull value="Others" TCStatus 
| fillnull value="0" IterationStartDate, ExecutionDate 
| fillnull value="Not Defined" TestCaseID, TestPlanID, Verdict,`std_getReleaseAttribute`, SatisfiedByRelease, SatisfiesRelease 
| dedup ModuleID, REQID, LinkStart_URL, TestCaseID sortby -ReleaseNone,-LinkValidity, -TCValidity 
| eval ReqTypeClassification = if((`prj_getSysRS`), "SYS", "DRS") 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval Valid_WorkitemID = if(WorkitemID!="Not Defined",WorkitemID, "Not Linked") 
| eventstats values(Valid_WorkitemID) delim=";" as linked_Implemented by ModuleID,REQID,LinkStart_URL, ReleaseNone 
| eval Valid_TestCaseID = if(TestCaseID!="Not Defined",TestCaseID, null()) 
| eval Implemented_URL = if((NOT like(Implemented_URL,"%oslc_config%")) AND like(Implemented_URL, "https://rb-alm-__-p.de.bosch.com/ccm/%"), Implemented_URL.$gcURL$, Implemented_URL) 
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0) 
| eventstats count(eval(ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed")  AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress")  AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted",
    values(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by ModuleID,LinkStart_URL, REQID 
| nomv Test_Case_Linked_temp 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| eval 12_Total = if(like(ReqDomain,"$domain$"), Requirements_To_Be_Processed, 0),
    12_Actual = if(like(ReqDomain,"$domain$"), Requirements_Linked_To_Source, 0),
    11_Total = if("$domain$"="%%%", Requirements_To_Be_Processed, if(Requirements_To_Be_Processed&gt;0 AND ((like(Domains,"$domain$") AND "$domain$"!="%SYS%" AND ReqTypeClassification="DRS") OR ((like(Domains,"%Not Defined%") OR like(Domains,"%SYS%")) AND "$domain$"="%SYS%")), Requirements_To_Be_Processed, 0)),
    11_Actual = if("$domain$"="%%%", Accepted_Requirements, if(Accepted_Requirements&gt;0 AND ((like(Domains,"$domain$") AND "$domain$"!="%SYS%" AND ReqTypeClassification="DRS") OR ((like(Domains,"%Not Defined%") OR like(Domains,"%SYS%")) AND "$domain$"="%SYS%")), Accepted_Requirements, 0)),
    13_Total = if(like(ReqDomain,"$domain$"), Requirements_To_Be_Tested, 0),
    13_Actual = if(like(ReqDomain,"$domain$"), Requirement_To_Be_Tested_Linked, 0),
    3_Total = if(like(ReqDomain,"$domain$"), Requirements_To_Be_Tested, 0),
    3_Actual=if((Requirements_To_Be_Tested&gt;0 AND Verdict="PASSED" AND like(ReqDomain,"$domain$")), 1, 0) 
| eval LinkStart_URL = if((NOT like(LinkStart_URL,"%oslc_config%")) AND like(LinkStart_URL, "https://rb-alm-__-p.de.bosch.com/rm/%"), LinkStart_URL.$gcURL$, LinkStart_URL ),
    LinkEnd_URL = if((NOT like(LinkEnd_URL,"%oslc_config%")) AND like(LinkEnd_URL, "https://rb-alm-__-p.de.bosch.com/qm/%"), LinkEnd_URL.$gcURL$, LinkEnd_URL),
    12_Actual_old = '12_Actual',
    12_Actual = if(((match(",".SatisfiesRelease.",","$release$") AND (match(",".SatisfiesLinkRelease.",","$release$") OR SatisfiesLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND SatisfiesLinkReleaseNone=1)) AND (match(",".SatisfiesVariant.",", "$variant$")) , '12_Actual', 0) 
| eval 3_Pending = '3_Total' - '3_Actual',
    11_Pending = '11_Total' - '11_Actual',
    12_Pending = '12_Total' - '12_Actual',
    13_Pending = '13_Total' - '13_Actual' 
| where ('$form.selectedMetrics$'&gt;0) 
| eval metricID=mvindex(split("$form.selectedMetrics$","_"),0) 
| lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains
    </query>
    <done>
      <set token="sysBasesid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <!-- SysArchRS TC query -->
  <search id="SysArcsearch" depends="$sys_arch_total_domain$">
    <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_STD_Quality_Dashboard_System_Architecture" OR source="Summary_STD_Quality_Dashboard_System_Integration_Test")
      | where _time=max(_time) 
      | eval Security = lower(Security), Legal = lower(Legal) 
      | eval 14_Total = SysArc_14_Ratio_of_defined_system_interfaces_linked_to_at_least_one_test_case_Total, 
            14_Actual = SysArc_14_Ratio_of_defined_system_interfaces_linked_to_at_least_one_test_case_Value,
            2_Total = SysInt_2_Ratio_of_system_interfaces_successfully_verified_Total, 
            2_Actual = SysInt_2_Ratio_of_system_interfaces_successfully_verified_Value 
      | where ('$form.selectedMetrics$'&gt;0) 
      | eval LinkStart_URL = if(like(LinkStart_URL,"%oslc_config%"), LinkStart_URL ,LinkStart_URL.$gcURL$),
          LinkEnd_URL = if(like(LinkEnd_URL,"%oslc_config%"), LinkEnd_URL ,LinkEnd_URL.$gcURL$)
      | eval metricID=mvindex(split("$form.selectedMetrics$","_"),0)
      | lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains
    </query>
    <done>
      <set token="sysBaseArchsid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <!-- SwRS TC search -->
  <search id="SWReqsearch" depends="$sw_total_domain$,$query1$">
    <query> 
      (index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_Software_Requirements" 
| where _time=max(_time) 
| fillnull value="" Contents
| fillnull value="Not Defined" `std_getReleaseAttribute`, SatisfiesRelease, SatisfiesLinkRelease, DesignLinkRelease, RQM_TestArtifacts, ProblemOrChangeReq, Team, TraceLinkRelease, RefineLinkRelease, Variant, SatisfiesVariant, `std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval  SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked")
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiedByLinkReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone, TraceLinkReleaseNone, RefineLinkReleaseNone
| rename `std_getStkhModule` as stkhModule
| eval stRSProcessed = split(stkhModule,"; ")
| eval stRSReleaseFiltered = mvfilter((match(",".mvindex(split(stRSProcessed,"["),1).",","$release$") AND ".*"!="$release$") OR (".*"="$release$" AND match(",".mvindex(split(stRSProcessed,"["),1).",",",ReleaseNone,")) OR (" * "==" $stRSModule$ "))
| eval stRSFiltered = mvfilter(match(" ".stRSReleaseFiltered." "," $stRSModule$ "))
| where ($plannedfor$) AND like(ReqDomain,"$domain$") AND ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".Variant.",", "$variant$")) AND isnotnull(stRSFiltered)
| table DNGConfiguration_ID, DNGLocalConfigurationName, GCConfigurationID, DNGComponent_ID, 
    ModuleID, ModuleName, ModuleType, REQID, Contents, LinkStart_URL, ReqType, Domains, Status, Safety, Security, Legal, User_Function, Verification_Level, SW_Function, SW_Comp, SYS_Function, ReqDomain, ReqType, ProblemOrChangeReq, Team,
    PlannedFor, `std_getReleaseAttribute`, ReleaseNone, 
    SatisfiesURL, SatisfiesREQID, SatisfiesRelease, SatisfiesLinkRelease, SatisfiesLinkReleaseNone,  
    Design_Link_Type, DesignLinkRelease, DesignLinkReleaseNone, "Architectural_Element_Linked",
    Trace_Link_Type, TraceLinkRelease, TraceLinkReleaseNone, "Trace_Element_Linked",
    Refine_Link_Type, RefineLinkRelease, RefineLinkReleaseNone, "Refine_Element_Linked", 
    RQM_TestArtifacts, TC_Count, NoTestcase,
    Requirements_To_Be_Processed, Accepted_Requirements, 
    Requirements_Linked_To_Source, 
    Requirements_To_Be_Tested, Requirement_To_Be_Tested_Linked,Implement_details,SWInt_21_Performance_CPU_to_be_tested_Total,SWInt_22_Performance_RAM_to_be_tested_Total,SWInt_22_Performance_ROM_to_be_tested_Total,Resource , Variant, SatisfiesVariant  
    
| eval Architectural_Element_Linked = if((((match(",".DesignLinkRelease.",",".*") OR DesignLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND DesignLinkReleaseNone=1)) , Architectural_Element_Linked, "Not Linked"),
    Trace_Element_Linked = if((((match(",".TraceLinkRelease.",",".*") OR TraceLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND TraceLinkReleaseNone=1)) , Trace_Element_Linked, "Not Linked"),
    Refine_Element_Linked = if((((match(",".RefineLinkRelease.",",".*") OR RefineLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND RefineLinkReleaseNone=1)) , Refine_Element_Linked, "Not Linked") 

| makemv delim="||" RQM_TestArtifacts 
| mvexpand RQM_TestArtifacts 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,".,"),
    ValidatedByLinkRelease=mvindex(RQM_TestArtifacts,12),
    ValidatedByLinkReleaseNone=mvindex(RQM_TestArtifacts,13),
    TCERRelease=mvindex(RQM_TestArtifacts,14),
    TCERReleaseNone=mvindex(RQM_TestArtifacts,15),
    TRRelease=mvindex(RQM_TestArtifacts,17),
    TRReleaseNone=mvindex(RQM_TestArtifacts,18),
    TCRelease=mvindex(RQM_TestArtifacts,23),
    TCReleaseNone=mvindex(RQM_TestArtifacts,24),
    TC_Variant=mvindex(RQM_TestArtifacts,25) 
| fillnull value="Not Defined" ValidatedByLinkRelease, TCERRelease, TRRelease, TCRelease 
| fillnull value=1 ValidatedByLinkReleaseNone, TCERReleaseNone, TRReleaseNone, TCReleaseNone 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND (match(",".TC_Variant.",", "$variant$")), 1, 0),
    TCERValidity = if((((match(",".TCERRelease.",","$release$") OR TCERRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCERReleaseNone=1)) , 1, 0),
    TRValidity = if((((match(",".TRRelease.",","$release$") OR TRRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TRReleaseNone=1)) AND LinkValidity = 1 , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, mvindex(RQM_TestArtifacts,0), "Not Defined"),
    LinkEnd_URL=if(TCValidity=1, mvindex(RQM_TestArtifacts,1), "Not Defined"),
    TestCaseID=if(TCValidity=1, mvindex(RQM_TestArtifacts,2), "Not Defined"),
    TestCaseUUID=if(TCValidity=1, mvindex(RQM_TestArtifacts,3), "Not Defined"),
    TestCaseName=if(TCValidity=1, mvindex(RQM_TestArtifacts,4), "Not Defined"),
    TestSuiteID=if(TCValidity=1, mvindex(RQM_TestArtifacts,5), "Not Defined"),
    TestPlanID=if(TCValidity=1, mvindex(RQM_TestArtifacts,6), "Not Defined"),
    TCERID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,7), "Not Defined"),
    TCERWebID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,8), "Not Defined"),
    IterationID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,9), "Not Defined"),
    TCRID=if(TCERValidity=1, mvindex(RQM_TestArtifacts,10), "Not Defined"),
    Verdict=if(TRValidity=1, mvindex(RQM_TestArtifacts,11), "Not Defined"),
    IterationStartDate=if(TCERValidity=1, mvindex(RQM_TestArtifacts,16), "0"), 
    TCERCreationDate=if(isnull(mvindex(RQM_TestArtifacts,21)), IterationStartDate, mvindex(RQM_TestArtifacts,21)),
    ExecutionDate=if(isnull(mvindex(RQM_TestArtifacts,19)), IterationStartDate, if(TCERValidity=1, if(TRValidity=1, mvindex(RQM_TestArtifacts,19), TCERCreationDate), "0")), 
    LatestExecution=if(isnull(mvindex(RQM_TestArtifacts,20)), "(ND)", if(TRValidity=1, mvindex(RQM_TestArtifacts,20), "(ND)")),
    TCStatus=if(TCValidity=1, mvindex(RQM_TestArtifacts,22), "Others")
    `std_fillIterationID_Gaps` 
| eval testedInItr=if(((match(",".IterationID.",", "$testedVersion$")) AND TCERWebID!="Not Defined"),1,0) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,")
| eval Type = mvindex(Implement_details,0),
       WorkitemID = mvindex(Implement_details,1),
       Summary = mvindex(Implement_details,2),
       FiledAgainst = mvindex(Implement_details,3),
       Iteration = mvindex(Implement_details,4),
       Tags = mvindex(Implement_details,5),
       "Issuer Class" = mvindex(Implement_details,6),
       "Status_Workitem" = mvindex(Implement_details,7),
       "Safety_Workitem" = mvindex(Implement_details,8),
       "Security_Workitem" = mvindex(Implement_details,9),
       "Legal_Workitem" = mvindex(Implement_details,10),
       CreationDate = mvindex(Implement_details,11),
       ClosureDate = mvindex(Implement_details,12),
       Implemented_URL = mvindex(Implement_details,13) 

| fillnull value="Others" TCStatus
| fillnull value="0" IterationStartDate, ExecutionDate 
| fillnull value="Not Defined" TestCaseID,TestPlanID,Verdict 
| dedup ModuleID, REQID, LinkStart_URL, TestCaseID sortby -ReleaseNone,-LinkValidity, -TCValidity, -testedInItr, -$testedVersionDate$, -TCERValidity, -TCERWebID, -TRValidity, -TCRID 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0)
| eval Implemented_URL = if((NOT like(Implemented_URL,"%oslc_config%")) AND like(Implemented_URL, "https://rb-alm-__-p.de.bosch.com/qm/%"), Implemented_URL.$gcURL$, Implemented_URL)
| eval Valid_WorkitemID = if(WorkitemID!="Not Defined",WorkitemID, "Not Linked") 
| eventstats values(Valid_WorkitemID) delim=";" as linked_Implemented by ModuleID,REQID,LinkStart_URL, ReleaseNone
| eval Valid_TestCaseID = if(TestCaseID!="Not Defined",TestCaseID, null())
| eventstats count(eval(ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval(Verdict="com.ibm.rqm.execution.common.state.passed" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval(Verdict="com.ibm.rqm.execution.common.state.error" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.blocked" OR Verdict="com.ibm.rqm.execution.common.state.paused" OR Verdict="com.ibm.rqm.execution.common.state.incomplete" OR Verdict="com.ibm.rqm.execution.common.state.inconclusive" OR Verdict="com.ibm.rqm.execution.common.state.partiallyblocked" OR Verdict="com.ibm.rqm.execution.common.state.deferred" OR Verdict="Not Defined" OR Verdict="com.ibm.rqm.execution.common.state.inprogress") AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted" ,
    list(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by ModuleID,LinkStart_URL, REQID 
| nomv Test_Case_Linked_temp 
    ``` 
| eval Test_Case_Linked_temp=Test_Case_Linked_temp.";" 
| rex field=Test_Case_Linked_temp max_match=0 "(?&lt;Test_Case_Linked&gt;(?: 
    [ \d]+;){1,10})"``` 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| eval 16_Total = Requirements_To_Be_Processed,
    16_Actual = Requirements_Linked_To_Source,
    15_Total = Requirements_To_Be_Processed,
    15_Actual = Accepted_Requirements,
    17_Total = Requirements_To_Be_Tested,
    17_Actual = Requirement_To_Be_Tested_Linked,
    6_Total = Requirements_To_Be_Tested,
    6_Actual = if((Requirements_To_Be_Tested&gt;0 AND Verdict="PASSED"),1,0),
    21_Total = SWInt_21_Performance_CPU_to_be_tested_Total,
    21_Actual = if((SWInt_21_Performance_CPU_to_be_tested_Total&gt;0 AND Verdict="PASSED"),1,0),
    22_Total_Ram = SWInt_22_Performance_RAM_to_be_tested_Total,
    22_Actual_Ram = if((SWInt_22_Performance_RAM_to_be_tested_Total&gt;0 AND Verdict="PASSED"),1,0),
    22_Total_Rom = SWInt_22_Performance_ROM_to_be_tested_Total,
    22_Actual_Rom = if((SWInt_22_Performance_ROM_to_be_tested_Total&gt;0 AND Verdict="PASSED"),1,0)
| eval LinkStart_URL = if((NOT like(LinkStart_URL,"%oslc_config%")) AND like(LinkStart_URL, "https://rb-alm-__-p.de.bosch.com/rm/%"), LinkStart_URL.$gcURL$, LinkStart_URL ),
    LinkEnd_URL = if((NOT like(LinkEnd_URL,"%oslc_config%")) AND like(LinkEnd_URL, "https://rb-alm-__-p.de.bosch.com/qm/%"), LinkEnd_URL.$gcURL$, LinkEnd_URL) 
| eval 16_Actual_old = '16_Actual'
| eval 16_Actual = if(((match(",".SatisfiesRelease.",","$release$") AND (match(",".SatisfiesLinkRelease.",","$release$") OR SatisfiesLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND SatisfiesLinkReleaseNone=1)) AND (match(",".SatisfiesVariant.",", "$variant$")),'16_Actual',0) ```,
    17_Actual = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) ,'17_Actual',0) ```
| eval 6_Pending = '6_Total' - '6_Actual',
    15_Pending = '15_Total' - '15_Actual',
    16_Pending = '16_Total' - '16_Actual',
    17_Pending = '17_Total' - '17_Actual',
    21_Pending = '21_Total' - '21_Actual',
    22_Pending_Ram = '22_Total_Ram' - '22_Actual_Ram',
    22_Pending_Rom = '22_Total_Rom' - '22_Actual_Rom'
| where ('$form.selectedMetrics$'&gt;0) 
| eval metricID=mvindex(split("$form.selectedMetrics$","_"),0) 
| lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains  
    </query>
    <done>
      <set token="swreqsid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <!-- SwRS TC search -->
  <search id="SWReqsearch2" depends="$sw_total_domain$,$query2$">
    <query> (index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_Software_Requirements" 
| where _time=max(_time) 
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, SatisfiesRelease, SatisfiesLinkRelease, DesignLinkRelease, RQM_TestArtifacts, ProblemOrChangeReq, Team, TraceLinkRelease, RefineLinkRelease, Variant, SatisfiesVariant, `std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiedByLinkReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone, TraceLinkReleaseNone, RefineLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
| eval stRSReleaseFiltered = mvfilter((match(",".mvindex(split(stRSProcessed,"["),1).",","$release$") AND ".*"!="$release$") OR (".*"="$release$" AND match(",".mvindex(split(stRSProcessed,"["),1).",",",ReleaseNone,")) OR (" * "==" $stRSModule$ "))
| eval stRSFiltered = mvfilter(match(" ".stRSReleaseFiltered." "," $stRSModule$ ")) 
| where ($plannedfor$) AND like(ReqDomain,"$domain$") AND ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) AND isnotnull(stRSFiltered) 
| table ModuleID, ModuleName, ModuleType, `std_getStkhModule`, REQID, Contents, LinkStart_URL, ReqType, Domains, Status, Safety, Security, Legal, 
    User_Function, Verification_Level, SW_Function, SW_Comp, SYS_Function, ReqDomain, ProblemOrChangeReq, Team,
    PlannedFor, `std_getReleaseAttribute`, ReleaseNone, 
    SatisfiesURL, SatisfiesREQID, SatisfiesRelease, SatisfiesLinkRelease, SatisfiesLinkReleaseNone, 
    Design_Link_Type, DesignLinkRelease, DesignLinkReleaseNone, "Architectural_Element_Linked",
    Trace_Link_Type, TraceLinkRelease, TraceLinkReleaseNone, "Trace_Element_Linked",
    Refine_Link_Type, RefineLinkRelease, RefineLinkReleaseNone, "Refine_Element_Linked", 
    TC_Count, NoTestcase,
    Requirements_To_Be_Processed, Accepted_Requirements, Requirements_Reviewed_Ratio, 
    Requirements_Linked_To_Source, Requirements_Linked_To_Source_Ratio, 
    Requirements_To_Be_Tested, Requirement_To_Be_Tested_Linked, Requirements_To_Be_Tested_Ratio,Implement_details,
    SWInt_21_Performance_CPU_to_be_tested_Total, SWInt_22_Performance_RAM_to_be_tested_Total, SWInt_22_Performance_ROM_to_be_tested_Total,Resource,
    Variant, SatisfiesVariant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, 
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, TC_Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase 
| eval Architectural_Element_Linked = if((((match(",".DesignLinkRelease.",",".*") OR DesignLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND DesignLinkReleaseNone=1)) , Architectural_Element_Linked, "Not Linked"),
    Trace_Element_Linked = if((((match(",".TraceLinkRelease.",",".*") OR TraceLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND TraceLinkReleaseNone=1)) , Trace_Element_Linked, "Not Linked"),
    Refine_Element_Linked = if((((match(",".RefineLinkRelease.",",".*") OR RefineLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND RefineLinkReleaseNone=1)) , Refine_Element_Linked, "Not Linked") 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = $attributeToBeConsidered$ 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".TC_Variant.",", "$variant$") , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","$testedVersion$")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","$latestExecution$") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    TCERWebID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),1)),
    IterationID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "No Filter Match", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),2)),
    TCRID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),3)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4))
    `std_fillIterationID_Gaps` 
| eval testedInItr=if(((match(",".IterationID.",", "$testedVersion$")) AND TCERWebID!="Not Defined"),1,0) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,") 
| eval Type = mvindex(Implement_details,0),
    WorkitemID = mvindex(Implement_details,1),
    Summary = mvindex(Implement_details,2),
    FiledAgainst = mvindex(Implement_details,3),
    Iteration = mvindex(Implement_details,4),
    Tags = mvindex(Implement_details,5),
    "Issuer Class" = mvindex(Implement_details,6),
    "Status_Workitem" = mvindex(Implement_details,7),
    "Safety_Workitem" = mvindex(Implement_details,8),
    "Security_Workitem" = mvindex(Implement_details,9),
    "Legal_Workitem" = mvindex(Implement_details,10),
    CreationDate = mvindex(Implement_details,11),
    ClosureDate = mvindex(Implement_details,12),
    Implemented_URL = mvindex(Implement_details,13) 
| fillnull value="Others" TCStatus 
| fillnull value="0" IterationStartDate, ExecutionDate 
| fillnull value="Not Defined" TestCaseID,TestPlanID,Verdict 
| dedup ModuleID, REQID, LinkStart_URL, TestCaseID sortby -ReleaseNone,-LinkValidity, -TCValidity 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0) 
| eval Implemented_URL = if((NOT like(Implemented_URL,"%oslc_config%")) AND like(Implemented_URL, "https://rb-alm-__-p.de.bosch.com/qm/%"), Implemented_URL.$gcURL$, Implemented_URL)
| eval Valid_WorkitemID = if(WorkitemID!="Not Defined",WorkitemID, "Not Linked") 
| eventstats values(Valid_WorkitemID) delim=";" as linked_Implemented by ModuleID,REQID,LinkStart_URL, ReleaseNone 
| eval Valid_TestCaseID = if(TestCaseID!="Not Defined",TestCaseID, null()) 
| eventstats count(eval(ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed")  AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress")  AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted",
    list(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by ModuleID,LinkStart_URL, REQID 
| nomv Test_Case_Linked_temp 
    ``` 
| eval Test_Case_Linked_temp=Test_Case_Linked_temp.";" 
| rex field=Test_Case_Linked_temp max_match=0 "(?&lt;Test_Case_Linked&gt;(?: 
    [ \d]+;){1,10})"``` 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| eval 16_Total = Requirements_To_Be_Processed,
    16_Actual = Requirements_Linked_To_Source,
    15_Total = Requirements_To_Be_Processed,
    15_Actual = Accepted_Requirements,
    17_Total = Requirements_To_Be_Tested,
    17_Actual = Requirement_To_Be_Tested_Linked,
    6_Total = Requirements_To_Be_Tested,
    6_Actual = if((Requirements_To_Be_Tested&gt;0 AND Verdict="PASSED"),1,0),
    21_Total = SWInt_21_Performance_CPU_to_be_tested_Total,
    21_Actual = if((SWInt_21_Performance_CPU_to_be_tested_Total&gt;0 AND Verdict="PASSED"),1,0),
    22_Total_Ram = SWInt_22_Performance_RAM_to_be_tested_Total,
    22_Actual_Ram = if((SWInt_22_Performance_RAM_to_be_tested_Total&gt;0 AND Verdict="PASSED"),1,0),
    22_Total_Rom = SWInt_22_Performance_ROM_to_be_tested_Total,
    22_Actual_Rom = if((SWInt_22_Performance_ROM_to_be_tested_Total&gt;0 AND Verdict="PASSED"),1,0) 
| eval LinkStart_URL = if((NOT like(LinkStart_URL,"%oslc_config%")) AND like(LinkStart_URL, "https://rb-alm-__-p.de.bosch.com/rm/%"), LinkStart_URL.$gcURL$, LinkStart_URL ),
    LinkEnd_URL = if((NOT like(LinkEnd_URL,"%oslc_config%")) AND like(LinkEnd_URL, "https://rb-alm-__-p.de.bosch.com/qm/%"), LinkEnd_URL.$gcURL$, LinkEnd_URL) 
| eval 16_Actual_old = '16_Actual' 
| eval 16_Actual = if(((match(",".SatisfiesRelease.",","$release$") AND (match(",".SatisfiesLinkRelease.",","$release$") OR SatisfiesLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND SatisfiesLinkReleaseNone=1)) AND (match(",".SatisfiesVariant.",", "$variant$")),'16_Actual',0) ```,
    17_Actual = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) ,'17_Actual',0) ```
| eval 6_Pending = '6_Total' - '6_Actual',
    15_Pending = '15_Total' - '15_Actual',
    16_Pending = '16_Total' - '16_Actual',
    17_Pending = '17_Total' - '17_Actual',
    21_Pending = '21_Total' - '21_Actual',
    22_Pending_Ram = '22_Total_Ram' - '22_Actual_Ram',
    22_Pending_Rom = '22_Total_Rom' - '22_Actual_Rom'
| where ('$form.selectedMetrics$'&gt;0) 
| eval metricID=mvindex(split("$form.selectedMetrics$","_"),0) 
| lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains
    </query>
    <done>
      <set token="swreqsid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <!-- SwArchRS search -->
  <search id="SWArcsearch" depends="$swArc_total_domain$">
    <query> (index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_STD_Quality_Dashboard_Software_Architecture" OR source="Summary_STD_Quality_Dashboard_Software_Integration_Test")
      | where _time=max(_time) 
      | eval Security = lower(Security), Legal = lower(Legal) 
      | eval 18_Total = SWArc_18_Ratio_of_software_interfaces_linked_to_at_least_one_test_case_Total, 
            18_Actual = SWArc_18_Ratio_of_software_interfaces_linked_to_at_least_one_test_case_Value,
            5_Total = SWInt_5_Ratio_of_software_interfaces_successfully_verified_Total, 
            5_Actual = SWInt_5_Ratio_of_software_interfaces_successfully_verified_Value 
      | where ('$form.selectedMetrics$'&gt;0) 
      | eval LinkStart_URL = if(like(LinkStart_URL,"%oslc_config%"), LinkStart_URL ,LinkStart_URL.$gcURL$),
          LinkEnd_URL = if(like(LinkEnd_URL,"%oslc_config%"), LinkEnd_URL ,LinkEnd_URL.$gcURL$)
      | eval metricID=mvindex(split("$form.selectedMetrics$","_"),0)
      | lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains
    </query>
    <done>
      <set token="swArcsid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <!--<search id="SWUnitsearch">
    <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) searchname="Summary_STD_Quality_Details_Software_Units_Verification"
        | table ModuleID,REQID, Contents, Status_CRS, Safety, Security, Legal, Verification_Level,Test_Case_Linked, Verdict,Status_CRS, Safety, Security, Legal,Domains,PlannedFor,ReqDomain,SatisfiedByURL,Status,ReqType,ModuleType,TestCaseID,TestPlanID,relevance,TC_Count,Error_Number,IterationID,LinkStart_URL,TestCaseName,LinkEnd_URL,Error_Number,ValidatedByLinkName,SWUni_24_Number_of_C_functions_with_unsatisfactory_code_complexity_Cyclomatic_Complexity_Value,SWUni_20_Ratio_of_software_units_successfully_verified_Total,SWUni_20_Ratio_of_software_units_successfully_verified_Value
        </query>
    <done>
      <set token="swUnitsid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>
  <search id="SWMisasearch">
    <query> (index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) search_name=Summary_STD_Quality_Details_Software_Units_Verification
          | fillnull value="Not Defined" Safety,Security,Legal,PlannedFor,Domains,IterationID,ReqDomain,SatisfiesURL
              `std_fillIterationID_Gaps` `std_fillPlannedFor_Gaps`
          | rename Verification_Level as "Verification Level",Test_Case_Linked as "Test Case Linked" 
          | fillnull value="NA" Verdict
          | fillnull value="Not linked by test case" "Test Case Linked"
     | eval relevance=if($testedVersion$ , 1, 0) 
      | eval Verdict=if(relevance==1,Verdict,"NA") 
      | table *
        </query>
    <done>
      <set token="swMisasid">$job.sid$</set>
    </done>
    <earliest>$date_earliest$</earliest>
    <latest>$date_latest$</latest>
  </search>-->
  <fieldset submitButton="true">
    <input type="dropdown" token="release" searchWhenChanged="true" id="release_id">
      <label>$releaseLabel$</label>
      <choice value=".*">None</choice>
      <default>.*</default>
      <initialValue>.*</initialValue>
      <fieldForLabel>ReleaseLabel</fieldForLabel>
      <fieldForValue>Release</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_STD_Developer_Dashboard_CRS_Search" OR source="Summary_STD_Developer_Dashboard_ReqMetric_SYS_DRS" OR source="Summary_STD_Developer_Dashboard_SW_Code_Quality") 
| where _time=max(_time) 
| rename `std_getReleaseAttribute` as Release 
| eval Release=split(Release, ",") 
| mvexpand Release 
| fillnull value="Not Defined" Release
| append [| makeresults | eval Release="Not Defined"]
| eval Release = trim(Release) 
| where NOT (like(Release,"%Default%") OR Release="Not in meta data") 
| dedup Release 
| where Release != "" AND Release != "-" AND Release != "0" 
| sort Release 
| table Release 
| eval ReleaseLabel = Release,
    ReleaseValueEscaped = replace(Release, "[.*+?|(){}[\]\\\^$]", "\\\\\\0"),
    ReleaseValue = if(like(ReleaseValueEscaped,"%|%"), ",".trim(mvindex(split(ReleaseValueEscaped, "\|"),0)).",|,".ReleaseValueEscaped."," ,",".ReleaseValueEscaped.",|,".ReleaseValueEscaped." \| Default,") 
| eval Release= ReleaseValue 
| table ReleaseLabel, Release</query>
        <earliest>$date_earliest$</earliest>
        <latest>$date_latest$</latest>
      </search>
      <change>
        <set token="release_Label">$row.ReleaseLabel$</set>
      </change>
    </input>
    <input type="multiselect" token="variant" id="variantMultiDropdown">
      <label>Variant</label>
      <choice value=".*">All</choice>
      <fieldForLabel>TC_Variant</fieldForLabel>
      <fieldForValue>TC_Variant</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw" 
| where _time=max(_time) 
| table TC_Variant 
| dedup TC_Variant 
| makemv delim="," TC_Variant 
| mvexpand TC_Variant 
| fillnull value="Not Defined" TC_Variant
| append [| makeresults | eval TC_Variant="Not Defined"]
| dedup TC_Variant
| sort TC_Variant</query>
        <earliest>$date_earliest$</earliest>
        <latest>$date_latest$</latest>
      </search>
      <delimiter>|</delimiter>
      <default>.*</default>
      <initialValue>.*</initialValue>
      <valuePrefix>,</valuePrefix>
      <valueSuffix>,</valueSuffix>
    </input>
    <input id="dateDropdown" type="dropdown" token="date_earliest" searchWhenChanged="true">
      <selectFirstChoice>true</selectFirstChoice>
      <label>Date</label>
      <fieldForLabel>label</fieldForLabel>
      <fieldForValue>earliestToken</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex`) (source="Summary_STD_DataIndexLedger") 
| where db="QM_DB" 
| table db, label, earliestToken 
| eval today = strftime(now(), "%F") 
| eval compareTime = label 
| sort -label 
| dedup earliestToken 
| eventstats latest(earliestToken) as latestDate 
| fieldformat latestDate = strftime(latestDate, "%F") 
| fieldformat label = if(label=today, label." (Today)", label) 
| sort -earliestToken
| eval today = strftime(now(), "%F")
| eval compareTime = label
| dedup earliestToken
| eventstats latest(earliestToken) as latestDate
| fieldformat latestDate = strftime(latestDate, "%F")
| fieldformat label = if(label=today, label." (Today)", label)</query>
        <earliest>0</earliest>
        <latest>now</latest>
      </search>
      <change>
        <condition>
          <eval token="latestTime">$row.latestDate$</eval>
          <eval token="time">$row.compareTime$</eval>
          <eval token="date_latest">$value$+86400</eval>
          <set token="load_done">true</set>
          <eval token="background_color_token">if(isnull($background_color_token$) OR "false"==$load_done$,"#F2F4F5",if($time$ == $latestTime$,"#C2E59D","#FFC91D"))</eval>
          <eval token="font_style">if(isnull($font_style$) OR "false"==$load_done$,"normal",if($time$ == $latestTime$,"normal","italic"))</eval>
        </condition>
        <condition match="$load_done$==true">
          <set token="load_done">false</set>
        </condition>
      </change>
    </input>
    <input type="multiselect" token="Team_token" id="teamMultiDropdown">
      <label>Team</label>
      <choice value="%">All</choice>
      <default>%</default>
      <initialValue>%</initialValue>
      <fieldForLabel>Team</fieldForLabel>
      <fieldForValue>Team</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_architecture_sys_sw") 
| where _time=max(_time) 
| fillnull value="Not Defined" Applied_Stereotypes 
| rename Applied_Stereotypes as Team 
| table Team 
| makemv delim="," Team 
| mvexpand Team 
| eval Team=trim(Team) 
| dedup Team 
| table Team 
| sort 0 Team</query>
        <earliest>$date_earliest$</earliest>
        <latest>$date_latest$</latest>
      </search>
      <valuePrefix>like(", ".Team.",","%, "."</valuePrefix>
      <valueSuffix>,%")</valueSuffix>
      <delimiter> OR </delimiter>
      <prefix>(</prefix>
      <suffix>)</suffix>
    </input>
    <input type="text" token="reqID" id="reqIDtext" searchWhenChanged="false">
      <label>Requirement ID</label>
      <change>
        <condition match="'value'==&quot;All&quot;">
          <set token="reqID">*</set>
        </condition>
        <condition>
          <set token="reqID">$value$</set>
        </condition>
      </change>
      <initialValue>All</initialValue>
      <default>All</default>
    </input>
    <input type="multiselect" token="tcStatus" depends="$hidden$" id="tcStatusMultiDropdown">
      <label>Test Case Status</label>
      <choice value="*">Exclude obsolete</choice>
      <delimiter>,</delimiter>
      <fieldForLabel>TCStatus</fieldForLabel>
      <fieldForValue>TCStatus</fieldForValue>
      <search>
        <query>((index=`std_getBaseIndex` OR index=`std_getMUIndex`)  source=`RQM_STD_Testcase`) 
| eval TCStatus = case(TestCaseState="com.ibm.rqm.process.testcase.workflow.state.s1", "Released",
    TestCaseState="com.ibm.rqm.planning.common.retired", "Implemented",
    TestCaseState="com.ibm.rqm.planning.common.approved", "Spec Reviewed",
    TestCaseState="com.ibm.rqm.planning.common.underreview", "Specified",
    TestCaseState="com.ibm.rqm.planning.common.new", "New/Changed",
    1=1, "Others")
| fillnull value="Not Defined" TCStatus
| append [| makeresults | eval TCStatus="Not Defined"]
| dedup TCStatus
| sort TCStatus 
| table TCStatus</query>
        <earliest>$date_earliest$</earliest>
        <latest>$date_latest$</latest>
      </search>
      <default>*</default>
      <initialValue>*</initialValue>
      <valuePrefix>"</valuePrefix>
      <valueSuffix>"</valueSuffix>
    </input>
    <input id="testedversionMultiDropdown" type="multiselect" token="testedVersion" depends="$token_domain_overview$">
      <label>Tested Version</label>
      <choice value=".*">Last Result</choice>
      <default>.*</default>
      <initialValue>.*</initialValue>
      <fieldForLabel>IterationID</fieldForLabel>
      <fieldForValue>IterationID</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getMUIndex`)  source=`RQM_STD_TestCaseExecutionRecord`
    `std_fillIterationID_Gaps` 
| fillnull value="Not Defined" IterationID
| append [| makeresults | eval IterationID="Not Defined"]
| dedup IterationID 
| sort IterationID 
| table IterationID</query>
        <earliest>$date_earliest$</earliest>
        <latest>$date_latest$</latest>
      </search>
      <valuePrefix>,</valuePrefix>
      <valueSuffix>,</valueSuffix>
      <delimiter>|</delimiter>
    </input>
    <input type="multiselect" token="VerdictReq" searchWhenChanged="false" id="reqVerdict" depends="$token_domain_overview$">
      <label>Requirement Verdict</label>
      <choice value="%">All</choice>
      <choice value="PASSED">PASSED</choice>
      <choice value="FAILED">FAILED</choice>
      <choice value="NOT EXECUTED">NOT EXECUTED</choice>
      <choice value="NA">NA</choice>
      <fieldForLabel>ReqVerdict</fieldForLabel>
      <fieldForValue>ReqVerdict</fieldForValue>
      <valuePrefix>like(ReqVerdict,"</valuePrefix>
      <valueSuffix>")</valueSuffix>
      <delimiter> OR </delimiter>
      <default>%</default>
      <initialValue>%</initialValue>
    </input>
    <input type="text" token="field1" id="text">
      <label></label>
      <default>Precalculated data from</default>
      <initialValue>Precalculated data from</initialValue>
    </input>
    <input type="text" token="export" id="latestexport">
      <label></label>
      <default>$exportlatest$</default>
      <initialValue>$exportlatest$</initialValue>
    </input>
    <input type="multiselect" token="element_type">
      <label>Element Type</label>
      <default>SequenceDiagram</default>
      <delimiter>,</delimiter>
      <fieldForLabel>Element_Type</fieldForLabel>
      <fieldForValue>Element_Type</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_architecture_sys_sw") 
| dedup Element_Type 
| sort Element_Type
|table Element_Type</query>
        <earliest>-24h@h</earliest>
        <latest>now</latest>
      </search>
      <valuePrefix>"</valuePrefix>
      <valueSuffix>"</valueSuffix>
      <choice value="*">All</choice>
    </input>
    <input type="multiselect" token="submodelid">
      <label>Sub Model ID</label>
      <choice value="*">All</choice>
      <default>*</default>
      <initialValue>*</initialValue>
      <valuePrefix>"</valuePrefix>
      <valueSuffix>",</valueSuffix>
      <fieldForLabel>modelid</fieldForLabel>
      <fieldForValue>modelid</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_architecture_sys_sw") 
| where _time=max(_time) 
| fillnull value="Not Defined" "Sub Model ID" 
| rename "Sub Model ID" as modelid 
| table modelid 
| makemv delim="," modelid 
| mvexpand modelid 
| eval Team=trim(modelid) 
| dedup modelid 
| table modelid 
| sort 0 modelid</query>
        <earliest>-24h@h</earliest>
        <latest>now</latest>
      </search>
    </input>
    <input type="multiselect" token="component">
      <label>Component</label>
      <choice value="*">All</choice>
      <default>*</default>
      <initialValue>*</initialValue>
      <valuePrefix>"</valuePrefix>
      <valueSuffix>",</valueSuffix>
      <fieldForLabel>component</fieldForLabel>
      <fieldForValue>component</fieldForValue>
      <search>
        <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) (source="Summary_architecture_sys_sw") 
| where _time=max(_time) 
| fillnull value="Not Defined" Component 
| rename Component as component 
| table component 
| makemv delim="," component 
| mvexpand component 
| eval Team=trim(component) 
| dedup component 
| table component 
| sort 0 component</query>
        <earliest>-24h@h</earliest>
        <latest>now</latest>
      </search>
    </input>
  </fieldset>
  <row id="topBannerStrip">
    <panel>
      <html>
      <img style="height:13px;width:100%" src="/static/app/XC_AN_Standard_v1/Bosch-Supergraphic-RGB-slim.png"/>
    </html>
    </panel>
  </row>
  <row depends="$TOOLTIP_LOGIC$">
    <panel>
      <title></title>
      <table>
        <search>
          <done>
            <set token="crsReqImpl_CR_/_P_linked">$result.QM_DEV_CR_/_P_linked$</set>
            <set token="SwRSid_CR_/_P_linked">$result.QM_DEV_CR_/_P_linked$</set>
            <set token="SysRSid_CR_/_P_linked">$result.QM_DEV_CR_/_P_linked$</set>
            <set token="crsid_CR_/_P_linked">$result.QM_DEV_CR_/_P_linked$</set>
          </done>
          <query>| inputlookup "Quality_Management_Metric_Definition.csv" 
| fields Metric_Name,Metric_Definition 
| transpose 0 header_field=Metric_Name</query>
          <earliest>-24h@h</earliest>
          <latest>now</latest>
        </search>
        <option name="drilldown">none</option>
        <option name="refresh.display">progressbar</option>
      </table>
    </panel>
  </row>
  <row depends="$STYLES$">
    <panel>
      <html>
        <style>
          #panelCrs .fieldset,#panelSysArch .fieldset,#panelSys .fieldset,#panelDrsHsi .fieldset,#panelSW .fieldset,#panelSwArc .fieldset{
            padding-bottom: 10px !important;
            margin-bottom: 0px !important;
            min-height: 50px !important;
            
          }
         #text .TextStyles__StyledInputWrapper-eg7n6t-3,#latestexport .TextStyles__StyledInputWrapper-eg7n6t-3 {
          padding: 0px !important;
          }
          @media only screen  and (min-width: 2200px)  {
            #text,#latestexport {
              top: 0px;
            }
          }
          #text {
           float: right;
           width: 145px !important;
           right: 145px;
           position: absolute;
           z-index: 99;
          }
          #latestexport {
           float: right;
           width: 150px;
           right: 0px;
           position: absolute;
          }
           #text .splunk-choice-input-message,#latestexport .splunk-choice-input-message {
           display:none;
          }
          #text .TextStyles__StyledInputWrapper-eg7n6t-3, #latestexport .TextStyles__StyledInputWrapper-eg7n6t-3{
            border: none !important;
            background-color: #f2f4f5;
            color: black;
            box-shadow: none;
            cursor:default;
          }
          
          #latestexport .iAgORy, #text .iAgORy{
           color: red;
          }
           #text .TextStyles__StyledInput-eg7n6t-4 ,#latestexport .TextStyles__StyledInput-eg7n6t-4 {
            font-size: 13px;
          }
          #latestexport .TextStyles__StyledInput-eg7n6t-4 {
            text-align:right;
          }
          .table td {
           padding: 6px 6px !important;
           text-align: left !important;
          }
          .table th {
           padding: 6px 6px !important;
           
          }
          #crsReqImpl td:nth-child(1),#crsReqImpl table tbody tr td:nth-child(3),#crsReqImpl table tbody tr td:nth-child(4),#crsReqImpl table tbody tr td:nth-child(5),#crsReqImpl table tbody tr td:nth-child(6),#crsReqImpl table tbody tr td:nth-child(7),#crsReqImpl table tbody tr td:nth-child(8),#crsReqImpl table tbody tr td:nth-child(9),#crsReqImpl table tbody tr td:nth-child(10),#crsReqImpl table tbody tr td:nth-child(11),#crsReqImpl table tbody tr td:nth-child(12),#crsReqImpl table tbody tr td:nth-child(13){
            cursor: default !important;
            color: #3c444d !important;
            width: 2% !important;
            overflow-wrap: anywhere !important;
            padding: 6px 6px !important;
          }
          #sysReqImpl table tbody tr td:nth-child(1),#sysReqImpl table tbody tr td:nth-child(3),#sysReqImpl table tbody tr td:nth-child(4),#sysReqImpl table tbody tr td:nth-child(5),#sysReqImpl table tbody tr td:nth-child(6),#sysReqImpl table tbody tr td:nth-child(7),#sysReqImpl table tbody tr td:nth-child(8),#sysReqImpl table tbody tr td:nth-child(9),#sysReqImpl table tbody tr td:nth-child(10),#sysReqImpl table tbody tr td:nth-child(11),#sysReqImpl table tbody tr td:nth-child(12),#sysReqImpl table tbody tr td:nth-child(13){
            cursor: default !important;
            color: #3c444d !important;
            width: 2% !important;
            overflow-wrap: anywhere !important;
            padding: 6px 6px !important;
          }
          #swReqImpl table tbody tr td:nth-child(1),#swReqImpl table tbody tr td:nth-child(3),#swReqImpl table tbody tr td:nth-child(4),#swReqImpl table tbody tr td:nth-child(5),#swReqImpl table tbody tr td:nth-child(6),#swReqImpl table tbody tr td:nth-child(7),#swReqImpl table tbody tr td:nth-child(8),#swReqImpl table tbody tr td:nth-child(9),#swReqImpl table tbody tr td:nth-child(10),#swReqImpl table tbody tr td:nth-child(11),#swReqImpl table tbody tr td:nth-child(12),#swReqImpl table tbody tr td:nth-child(13){
            cursor: default !important;
            color: #3c444d !important;
            width: 2% !important;
            overflow-wrap: anywhere !important;
            padding: 6px 6px !important;
          }
          #rowCrsImpl,#rowSysImpl,#rowSWImpl
          {
            border: 1px solid rgb(195, 203, 212);
            border-radius: 3px;
            background-color: white;
            margin-bottom: 5px;
           }
          
          #crsReqImpl td:nth-child(2),#sysReqImpl td:nth-child(2),#swReqImpl td:nth-child(2){
            text-decoration: underline #006eaa;
            width: 2% !important;
            padding: 6px 6px !important;
            text-align:left;
            color: #006eaa !important;
          }
          #crsReqImpl th:nth-child(2),#sysReqImpl th:nth-child(2),#swReqImpl th:nth-child(2){
            text-align:left;
            padding: 6px 6px !important;
            width: 1% !important;
          }
          #crsReqImpl td:nth-child(6),#sysReqImpl td:nth-child(6),#swReqImpl td:nth-child(6){
            width: 4% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
            width: 2% !important;
            padding: 6px 6px !important;
          }
          .hide-text{
            z-index: 9 !important;
          }
          .menus{
            z-index: 9 !important;
          }
          #topBannerStrip {
          margin-bottom: 21px;
        }
          .BoxStyles__Styled-sc-1h4b5f6-0 {
            max-height:115px !important;
           }
          .fieldset {
            margin-bottom: 0px;
          }
          @media only screen and (min-width: 960px)  {
             .navBar---pages-enterprise---8-2-10---3gUds{
              display: inline-flex;
              position: sticky !important;
             }
             [id*="panel"] .dashboard-panel {
             min-height:0px !important;
            }
            #topBannerStrip{
              z-index: 99;
              top: 280px;
              margin-bottom: 25px ;
            }
            #topBannerStrip .dashboard-panel .panel-body.html {
             
              background: #F2F4F5;
            }
           #rightBtnpanel {
              margin-top: 20px;
             }
            .dashboard-form-globalfieldset { 
                position: sticky !important;
                <!--top: 132px !important;-->
                min-height: 45px !important;
                max-height: 1500px;
              }  
             .dashboard-form-globalfieldset {
              background: #F2F4F5;
              position: sticky !important;
              
            }
            .dashboard-header {
               position: sticky !important;
               <!--top: 78px !important;-->
               height:40px;
               <!--margin-bottom:0px !important;-->
              padding-top:14px !important;
              }
               header {
                position: sticky !important;
              }
            }
            
            @media only screen  and (min-width: 0px) and (max-width: 960px)  {
             .navBar---pages-enterprise---8-2-10---3gUds{
              display: inline-flex;
              position: sticky !important;
             }
            #topBannerStrip .dashboard-panel .panel-body.html {
              position: sticky !important;
              width: 100% !important;
              margin-top: 0px;
            }
             [id*="panel"] .dashboard-panel {
             min-height:0px !important;
            }
           
            .dashboard-form-globalfieldset { 
                position: sticky !important;
                <!--top: 132px !important;-->
                min-height: 205px !important;
                max-height: 1500px;
                
               
              }  
             .dashboard-form-globalfieldset {
              background: #F2F4F5;
              position: sticky !important;
              width: 100% !important;
            }
            
            #topBannerStrip{
              position: sticky !important;
              z-index: 99;
              top: 353px;
              height: 13px;
              margin-top: -2px !important;
              margin-bottom: 22px;
             
            }
            .dashboard-header {
               position: sticky !important;
               <!--top: 78px !important;-->
               height: 40px !important;
               padding-top: 14px !important;
               margin-bottom:0px !important;
              }
              #rightBtnpanel {
                margin-top:8px !important;
              }
              header {
                position: sticky !important;
              }
             }
          #topBannerStrip .dashboard-panel .panel-body.html {
             position: fixed;
             z-index: 99;
             width:calc(100% - 40px);
             background: #F2F4F5;
           }
          #rightBtnpanel {
              height:100%;
          }
        .dashboard-form-globalfieldset { 
          position: fixed;
          z-index: 99;
          background: #F2F4F5;
          display: inline-flex;
          <!--top: 132px;-->
          min-height: 50px;
          flex-wrap: wrap;
           width: 100.1% !important;
          
          }
         header {
            display: block;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 999;
          }
         .dashboard-header {
            margin-bottom: 10px;
            padding-top: 14px;
            min-height: 28px;
            position: fixed;
            width: 100.1%;
            z-index: 99;
            background: #F2F4F5;
            <!--top: 78px;-->
          }
          #topBannerStrip {
            width: 100.1%;
          }
          .hide-global-filters {
            position:relative;
          }
    
          h1 {
             margin: 10px 0px 0px 0px !important;
          }
          .fieldset .input{
              width: auto;
          }
          .fieldset {
            margin-bottom: -10px ;
          }
          #submit{
            position:relative;
          }
          .fieldset .form-submit {
            padding-bottom: 15px;
          }
          #dateDropdown .SelectBaseStyles__StyledButton-sc-16cj7sk-0 {
            background-color: $background_color_token$ !important;
            color: #171d21 !important;
            font-style: $font_style$ !important;
          }
          
          table tbody tr td {
            color: #3c444d !important;
            cursor: default !important;
          } 
          #SysRSid table tbody tr td:nth-child(1),
          #SysRSid table tbody tr td:nth-child(4),
          #SysRSid table tbody tr td:nth-child(5),
          #SysRSid table tbody tr td:nth-child(6),
          #SysRSid table tbody tr td:nth-child(7),
          #SysRSid table tbody tr td:nth-child(8),
          #SysRSid table tbody tr td:nth-child(10),
          #SysRSid table tbody tr td:nth-child(12),
          #SysRSid table tbody tr td:nth-child(15),
          #SysRSid table tbody tr td:nth-child(16),
            #SysRSid table tbody tr td:nth-child(17){
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
            width: 5% !important;
          }
          
          #SysRSid table tbody tr td:nth-child(9) {
           overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
            width: 7% !important;
          }
          
          
          
          #SwRSid table tbody tr td:nth-child(1),
          #SwRSid table tbody tr td:nth-child(4),
          #SwRSid table tbody tr td:nth-child(5),
          #SwRSid table tbody tr td:nth-child(6),
          #SwRSid table tbody tr td:nth-child(7),
          #SwRSid table tbody tr td:nth-child(8),
          #SwRSid table tbody tr td:nth-child(13),
          #SwRSid table tbody tr td:nth-child(14),
          #SwRSid table tbody tr td:nth-child(15),
          
          #SwRSid table tbody tr td:nth-child(17),
          #SwRSid table tbody tr td:nth-child(18),
          #SwRSid table tbody tr td:nth-child(19)
          {
            width:5% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
          }
          #SwRSid table tbody tr td:nth-child(9)
          {
            width:8% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
          }
          
          
          
          #SwRSid table tbody tr td:nth-child(10),
          #SwRSid table tbody tr td:nth-child(11),
          #SwRSid table tbody tr td:nth-child(12)
          {
            width: 5.5% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
            text-align: left !important;
          }
          
          #SwRSid table tbody tr td:nth-last-child(4)
          {
            width:5% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
          }
          
          
          #SwArcRS table tbody tr td:nth-child(1)
          #SwArcRS table tbody tr td:nth-child(4),
          #SwArcRS table tbody tr td:nth-child(5),
          #SwArcRS table tbody tr td:nth-child(6),
          #SwArcRS table tbody tr td:nth-child(7),
          #SwArcRS table tbody tr td:nth-child(8),
          #SwArcRS table tbody tr td:nth-child(9),
          #SwArcRS table tbody tr td:nth-child(10),
          #SwArcRS table tbody tr td:nth-child(12){
            width:5% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
          }
         
          #SwArcRS table tbody tr td:nth-child(11){
            width:8% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
          }
          
          
          
          #SysRSid table tbody tr td:nth-child(3),
          #SysArchRSid table tbody tr td:nth-child(3),
          #SwRSid table tbody tr td:nth-child(3),
          #SwArcRS  table tbody tr td:nth-child(3) {
            
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
            width: 30% !important;
          }
          
          
          #SysRSid table tbody tr td:nth-child(2),
          #SysArchRSid table tbody tr td:nth-child(2),
          #SwRSid table tbody tr td:nth-child(2),
          #SwArcRS  table tbody tr td:nth-child(2) {
            color: #006eaa !important;
            text-decoration: underline #006eaa !important;
            cursor:pointer !important;
            width:4% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word;
            white-space: break-space;
          }
          
          
          #SysRSid table tbody tr td:nth-last-child(3),
          #SysArchRSid table tbody tr td:nth-last-child(3),
          #SwRSid table tbody tr td:nth-last-child(3),
          #SwArcRS  table tbody tr td:nth-last-child(3)
          {
            width:5% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word !important;
            white-space: unset;
          }
          
          #SysRSid table tbody tr td:nth-last-child(2),
          #SysArchRSid table tbody tr td:nth-last-child(2),
          #SwRSid table tbody tr td:nth-last-child(2),
          #SwArcRS  table tbody tr td:nth-last-child(2)
          {
            width:5% !important;
            overflow-wrap: anywhere !important;
            word-wrap: break-word !important;
            white-space: unset;
          }
          
          
          
          #resized_pcr1 div[data-component="splunk-core:/splunkjs/mvc/components/MultiDropdown"],
          #resized_pcr2 div[data-component="splunk-core:/splunkjs/mvc/components/MultiDropdown"]{
             width: 350px !important;
             margin-right: auto !important;
          }
          #testedversionMultiDropdown div[data-component="splunk-core:/splunkjs/mvc/components/MultiDropdown"]{
             width: 290px !important;
             margin-right: auto !important;
          }
          
          #crsid td:nth-child(2),
          #SysRSid td:nth-child(2),
          #SysRsTCid td:nth-child(1),
          #SysArchRSid td:nth-child(2),
          #SysArchRsTCid td:nth-child(1),
          #SwRSid td:nth-child(2),
          #SwRsTCid td:nth-child(1),
          #SwArcRS td:nth-child(2),
          #SwArcRsTCid td:nth-child(1)
          {
            color: #006eaa !important;
            text-decoration: underline #006eaa !important;
            cursor:pointer !important;
          }
          #crsid td:nth-child(3),#crsid th:nth-child(3) {
            width: 20%  !important;
            overflow-wrap:anywhere;
          }
          #crsid th:nth-child(12), #crsid td:nth-child(12) {
            width: 8%  !important;
            overflow-wrap:anywhere !important;
          }
      
          #crsid td:nth-child(1), #crsid th:nth-child(1), 
          #crsid td:nth-child(2), #crsid th:nth-child(2),
          #crsid td:nth-child(4),#crsid th:nth-child(4),
          #crsid td:nth-child(5),#crsid th:nth-child(5),
          #crsid td:nth-child(6),#crsid th:nth-child(6),
          #crsid td:nth-child(7),#crsid th:nth-child(7),
          #crsid td:nth-child(8),#crsid th:nth-child(8),
          #crsid td:nth-child(9),#crsid th:nth-child(9),
          #crsid td:nth-child(10),#crsid th:nth-child(10),
          #crsid td:nth-child(10),#crsid th:nth-child(11),
          #crsid td:nth-child(12),#crsid th:nth-child(13),
          #crsid td:nth-child(13),#crsid th:nth-child(14),
          #crsid td:nth-child(14),#crsid th:nth-child(15){
            width: 5%  !important;
            overflow-wrap:anywhere !important;
          }
          th:last-child, td:last-child {
            display: none;
          }
          
          .dashboard-cell {
            width: 100%  !important;
          }
          
          #topBannerStrip .dashboard-panel  {
            background: #F2F4F5 !important; 
          }
          #topBannerStrip .dashboard-panel .panel-body.html {
              padding : 0px 0px;
          }
          #topBannerStrip .panel-body  {
            background: #F2F4F5 !important; 
            padding-left:0px !important;
            padding-right:0px !important;
          }
          
          .splunk-table {
            width:98.5% !important;
            margin: auto;
            margin-bottom: 10px;
            border: 1px solid rgb(195, 203, 212);
            border-radius: 3px;
          }
          
          #crsidRow .dashboard-panel, 
          #SysRSidRow .dashboard-panel,
          #SysRsTCid .dashboard-panel,
          #SysArchRSid .dashboard-panel,
          #SysArchRsTCid .dashboard-panel,
          #SwRSidRow .dashboard-panel,
          #SwRsTCid .dashboard-panel,
          #SwArcRS .dashboard-panel,
          #SwArcRsTCid .dashboard-panel{
            border: 1px solid rgb(195, 203, 212);
            border-radius: 3px;
          }

        </style>
        </html>
    </panel>
  </row>
  <row depends="$Hidden$">
    <panel>
      <!-- Get domain values-->
      <table>
        <search id="getSelectedDomain">
          <finalized>
            <condition match="'job.resultCount' != 0">
              <set token="selectedDomain">$result.selectedDomain$</set>
              <set token="selectedDomainRegx">$result.selectedDomainRegx$</set>
            </condition>
          </finalized>
          <query>| makeresults 
| eval selectedDomain = "$form.domain_crs$" 
| eval selectedDomainRegx = replace(replace(selectedDomain, "%", ""), ",", "|"),
    temp = split(selectedDomainRegx,"|"), hiddenColumn=""
| eval total = mvcount(temp),
    filteredTotal = mvcount(mvfilter(match(temp,"SYS|Not Defined|SW|HW|ME"))) 
| eval others =if(isnull(filteredTotal) or trim(filteredTotal)="", total, total-filteredTotal)
| eval selectedDomainRegx=if(isnull(selectedDomainRegx) or trim(selectedDomainRegx)="", ".*", if(others&gt;0, selectedDomainRegx."|.*", selectedDomainRegx)) 
| table selectedDomain, selectedDomainRegx, hiddenColumn</query>
          <earliest>-24h@h</earliest>
          <latest>now</latest>
        </search>
        <option name="drilldown">none</option>
        <option name="refresh.display">progressbar</option>
      </table>
    </panel>
  </row>
  <row id="crsidRow" depends="$crs_total_domain$">
    <panel id="panelCrs " depends="$crs_total_domain$">
      <title>$name$ - BBMID $BBMID$ ($ASPICE$) : $infoMsg$ - &gt;  $CRS_done$</title>
      <input type="text" token="contentFiltercrs" searchWhenChanged="true">
        <label>Contents filter</label>
        <default></default>
      </input>
      <table id="crsid">
        <title>List of DNG IDs / List of requirements affected</title>
        <search depends="$crs_total_domain$">
          <done>
            <set token="CRS_done">$job.resultCount$</set>
          </done>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Details_Requirement_Elicitation" 
| where _time=max(_time) 
| fillnull value="" Contents
| fillnull value="Not Defined" `std_getReleaseAttribute`, SatisfactionRelease, SatisfiedBySysRelease, SatisfiedBySwRelease, SatisfiedByHwRelease, SatisfiedByMechRelease, SatisfiedByLinkSysRelease, SatisfiedByLinkSwRelease, SatisfiedByLinkHwRelease, SatisfiedByLinkMechRelease, SatisfiedByLinkRelease, PlannedFor, ProblemOrChangeReq, Team, Feature, ReqType, Variant, satisfiedByVariant, satisfiedBySysVariant, satisfiedBySwVariant, satisfiedByHwVariant, satisfiedByMechVariant,Stakeholder_ID
| fillnull value=1 ReleaseNone, SatisfiedByLinkReleaseNone, SatisfiedByLinkSysReleaseNone, SatisfiedByLinkSwReleaseNone, SatisfiedByLinkHwReleaseNone, SatisfiedByLinkMechReleaseNone 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval stkhModule = if(ReleaseNone=1, ModuleID." [,".Release.",ReleaseNone,]", ModuleID." [,".Release.",]")
| eval stRSProcessed = split(stkhModule,"; ")
| eval stRSReleaseFiltered = mvfilter((match(",".mvindex(split(stRSProcessed,"["),1).",","$release$") AND ".*"!="$release$") OR (".*"="$release$" AND match(",".mvindex(split(stRSProcessed,"["),1).",",",ReleaseNone,")) OR (" * "==" $stRSModule$ "))
| eval stRSFiltered = mvfilter(match(" ".stRSReleaseFiltered." "," $stRSModule$ "))
| search ($safety$) AND ($legal$) AND ($security$) AND (Status_CRS IN ($ReqStatus$)) AND (ModuleID IN $reqModule$) AND (REQID IN ($reqID$))
| where ($plannedfor$) AND ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (`std_getCusRS` OR ReqType="Not Defined") AND (match(",".TC_Variant.",", "$variant$")) AND isnotnull(stRSFiltered)
| eval relevance=if(match(",".IterationID.",", "$testedVersion$") , 1, 0) 
| eval Verdict=if(relevance==1,Verdict,"NA") 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,") 
| eval WorkitemID = mvindex(Implement_details,1)
| eval Valid_WorkitemID = if(WorkitemID!="Not Defined",WorkitemID, "Not Linked") 
| eventstats values(Valid_WorkitemID) delim=";" as linked_Implemented by ModuleID,REQID,LinkStart_URL, ReleaseNone
| dedup ModuleID, LinkStart_URL, REQID
    `std_fillIterationID_Gaps` `std_fillPlannedFor_Gaps` 
| eval 1_Total = CRS_Accepted_Total, 
    1_Actual = CRS_Accepted_Req,
    10_Total = CRS_Traceable_Total, 
    10_Actual = CRS_Traceable_Req 
| eval metricID=mvindex(split("$form.selectedMetrics$","_"),0) 
| lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains 
| eval LinkStart_URL = if((NOT like(LinkStart_URL,"%oslc_config%")) AND like(LinkStart_URL, "https://rb-alm-__-p.de.bosch.com/rm/%"), LinkStart_URL.$gcURL$, LinkStart_URL )
| where ($domain_crs$) AND ($Team_token$) AND ($feature$)
| search ($PCR_token$)
| eval SatisfiedByLinkRelease = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), SatisfiedByLinkRelease, if(like("$selectedDomain$", "%SYS%"), SatisfiedByLinkSysRelease,  if(like("$selectedDomain$", "%SW%"), SatisfiedByLinkSwRelease,  if(like("$selectedDomain$", "%HW%"), SatisfiedByLinkHwRelease, SatisfiedByLinkMechRelease)))),
    SatisfactionRelease = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), SatisfactionRelease, if(like("$selectedDomain$", "%SYS%"), SatisfiedBySysRelease,  if(like("$selectedDomain$", "%SW%"), SatisfiedBySwRelease,  if(like("$selectedDomain$", "%HW%"), SatisfiedByHwRelease, SatisfiedByMechRelease)))),
    SatisfiedByLinkReleaseNone = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), SatisfiedByLinkReleaseNone, if(like("$selectedDomain$", "%SYS%"), SatisfiedByLinkSysReleaseNone, if(like("$selectedDomain$", "%SW%"), SatisfiedByLinkSwReleaseNone, if(like("$selectedDomain$", "%HW%"), SatisfiedByLinkHwReleaseNone, SatisfiedByLinkMechReleaseNone)))),
    satisfiedByVariant = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), satisfiedByVariant, if(like("$selectedDomain$", "%SYS%"), satisfiedBySysVariant, if(like("$selectedDomain$", "%SW%"), satisfiedBySwVariant, if(like("$selectedDomain$", "%HW%"), satisfiedByHwVariant, satisfiedByMechVariant)))) 
| eval 10_Actual = if((((match(",".SatisfiedByLinkRelease.",","$release$") OR SatisfiedByLinkRelease="Not Defined") AND match(",".SatisfactionRelease.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND SatisfiedByLinkReleaseNone=1)) AND match(SatisfiedByReqType,"$selectedDomainRegx$") AND (match(",".satisfiedByVariant.",", "$variant$")),'10_Actual',0) 
| eval 1_Pending = '1_Total' - '1_Actual',
    10_Pending = '10_Total' - '10_Actual' 
| where ('$form.selectedMetrics$'&gt;0) 
| eval Contents = if(len(Contents)&gt;`std_getDDContentsCharLimit`, substr(Contents,1,`std_getDDContentsCharLimit`)."....", Contents) 
| where like(lower(Contents),lower("%$contentFiltercrs$%"))
| makemv linked_Implemented
| nomv linked_Implemented
| eval "CR / P linked"=replace(linked_Implemented,";", "; ") 
| rename ModuleID as "Module ID",REQID as "Req. ID" ,"Stakeholder_ID" as "Stakeholder Req. ID",Status_OEM as "Status OEM", ReqType as "Artifact Type"
| fillnull value="Not Defined" "Stakeholder Req. ID","Status OEM"
| search ("Stakeholder Req. ID" IN ($stkreqID$))
| table "Module ID", "Req. ID", Contents, "Artifact Type",Status_CRS,Feature,Domains, Safety, Security, Legal,Team,Release,Variant,"Stakeholder Req. ID","Status OEM","CR / P linked", LinkStart_URL</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="CR / P linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Req. ID&quot;">
            <link target="_blank">$row.LinkStart_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="rowCrsImpl" depends="$crs_total_domain$">
    <panel id="panelImplementedCrs">
      <title>Linked Change Request / Problem</title>
      <input type="multiselect" token="filedagainst" searchWhenChanged="true">
        <label>Filed Against</label>
        <choice value="%">All</choice>
        <default>%</default>
        <valuePrefix>like(FiledAgainst,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <fieldForLabel>FiledAgainst</fieldForLabel>
        <fieldForValue>FiledAgainst</fieldForValue>
        <search>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Details_Requirement_Elicitation" 
| where _time=max(_time) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,")
| eval FiledAgainst = mvindex(Implement_details,3)
| fillnull value="Not Defined" FiledAgainst
| append [| makeresults | eval FiledAgainst="Not Defined"]
| dedup FiledAgainst
| table  FiledAgainst</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
      </input>
      <input type="multiselect" token="workitemstatus" searchWhenChanged="true">
        <label>Work Item Status</label>
        <choice value="*">Exclude obsolete</choice>
        <default>*</default>
        <valuePrefix>"</valuePrefix>
        <valueSuffix>"</valueSuffix>
        <delimiter> , </delimiter>
        <fieldForLabel>Status</fieldForLabel>
        <fieldForValue>Status</fieldForValue>
        <search>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Details_Requirement_Elicitation"
| where _time=max(_time) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,")
| eval Status = mvindex(Implement_details,7)
| fillnull value="Not Defined" Status
| append [| makeresults | eval Status="Not Defined"]
| dedup Status
| table  Status</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
      </input>
      <table id="crsReqImpl">
        <search>
          <progress>
            <eval token="workitemidcrs">replace($PCR_token$,"ProblemOrChangeReq","WorkitemID")</eval>
          </progress>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Details_Requirement_Elicitation" 
| where _time=max(_time) 
| fillnull value="" Contents
| fillnull value="Not Defined" `std_getReleaseAttribute`, SatisfactionRelease, SatisfiedBySysRelease, SatisfiedBySwRelease, SatisfiedByHwRelease, SatisfiedByMechRelease, SatisfiedByLinkSysRelease, SatisfiedByLinkSwRelease, SatisfiedByLinkHwRelease, SatisfiedByLinkMechRelease, SatisfiedByLinkRelease, PlannedFor, ProblemOrChangeReq, Team, Feature, ReqType,FiledAgainst,Status,`std_getStkhModule`
| fillnull value=1 ReleaseNone, SatisfiedByLinkReleaseNone, SatisfiedByLinkSysReleaseNone, SatisfiedByLinkSwReleaseNone, SatisfiedByLinkHwReleaseNone, SatisfiedByLinkMechReleaseNone 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval stkhModule = if(ReleaseNone=1, ModuleID." [,".Release.",ReleaseNone,]", ModuleID." [,".Release.",]")
| eval stRSProcessed = split(stkhModule,"; ")
| eval stRSReleaseFiltered = mvfilter((match(",".mvindex(split(stRSProcessed,"["),1).",","$release$") AND ".*"!="$release$") OR (".*"="$release$" AND match(",".mvindex(split(stRSProcessed,"["),1).",",",ReleaseNone,")) OR (" * "==" $stRSModule$ "))
| eval stRSFiltered = mvfilter(match(" ".stRSReleaseFiltered." "," $stRSModule$ "))
| search ($safety$) AND ($legal$) AND ($security$) AND (Status_CRS IN ($ReqStatus$)) AND (ModuleID IN $reqModule$) AND (REQID IN ($reqID$))
| where ($plannedfor$) AND ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (`std_getCusRS` OR ReqType="Not Defined") AND isnotnull(stRSFiltered)
| fillnull value="Not Defined" "Stakeholder_ID"
| eval Stakeholder_ID = replace(Stakeholder_ID, "\s+", " ")
| rename "Stakeholder_ID" as "Stakeholder Req. ID"
| search ("Stakeholder Req. ID" IN ($stkreqID$))
| eval relevance=if(match(",".IterationID.",", "$testedVersion$") , 1, 0) 
| eval Verdict=if(relevance==1,Verdict,"NA") 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,")
| eval Type = mvindex(Implement_details,0),
       WorkitemID = mvindex(Implement_details,1),
       Summary = mvindex(Implement_details,2),
       FiledAgainst = mvindex(Implement_details,3),
       Iteration = mvindex(Implement_details,4),
       Tags = mvindex(Implement_details,5),
       "Issuer Class" = mvindex(Implement_details,6),
       "Status_Workitem" = mvindex(Implement_details,7),
       "Safety_Workitem" = mvindex(Implement_details,8),
       "Security_Workitem" = mvindex(Implement_details,9),
       "Legal_Workitem" = mvindex(Implement_details,10),
       CreationDate = mvindex(Implement_details,11),
       ClosureDate = mvindex(Implement_details,12),
       Implemented_URL = mvindex(Implement_details,13)
| eval Valid_WorkitemID = if(WorkitemID!="Not Defined",WorkitemID, "Not Linked") 
| eventstats values(Valid_WorkitemID) delim=";" as linked_Implemented by ModuleID,REQID,LinkStart_URL, ReleaseNone
| dedup ModuleID, LinkStart_URL, REQID
    `std_fillIterationID_Gaps` `std_fillPlannedFor_Gaps` 
| eval 1_Total = CRS_Accepted_Total, 
    1_Actual = CRS_Accepted_Req,
    10_Total = CRS_Traceable_Total, 
    10_Actual = CRS_Traceable_Req 
| eval metricID=mvindex(split("$form.selectedMetrics$","_"),0) 
| lookup "QMM_Template_Data.csv" ID AS metricID OUTPUTNEW Domains AS metricDomains 
| eval LinkStart_URL = if((NOT like(LinkStart_URL,"%oslc_config%")) AND like(LinkStart_URL, "https://rb-alm-__-p.de.bosch.com/rm/%"), LinkStart_URL.$gcURL$, LinkStart_URL )
| where ($domain_crs$) AND ($Team_token$) AND ($feature$) AND ($filedagainst$)
| search ($PCR_token$) AND (Status_Workitem IN ($workitemstatus$)) AND $workitemidcrs$
| eval Implemented_URL = if((NOT like(Implemented_URL,"%oslc_config%")) AND like(Implemented_URL, "https://rb-alm-__-p.de.bosch.com/ccm/%"), Implemented_URL.$gcURL$, Implemented_URL)
| eval SatisfiedByLinkRelease = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), SatisfiedByLinkRelease, if(like("$selectedDomain$", "%SYS%"), SatisfiedByLinkSysRelease,  if(like("$selectedDomain$", "%SW%"), SatisfiedByLinkSwRelease,  if(like("$selectedDomain$", "%HW%"), SatisfiedByLinkHwRelease, SatisfiedByLinkMechRelease)))),
    SatisfactionRelease = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), SatisfactionRelease, if(like("$selectedDomain$", "%SYS%"), SatisfiedBySysRelease,  if(like("$selectedDomain$", "%SW%"), SatisfiedBySwRelease,  if(like("$selectedDomain$", "%HW%"), SatisfiedByHwRelease, SatisfiedByMechRelease)))),
    SatisfiedByLinkReleaseNone = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), SatisfiedByLinkReleaseNone, if(like("$selectedDomain$", "%SYS%"), SatisfiedByLinkSysReleaseNone, if(like("$selectedDomain$", "%SW%"), SatisfiedByLinkSwReleaseNone,  if(like("$selectedDomain$", "%HW%"), SatisfiedByLinkHwReleaseNone, SatisfiedByLinkMechReleaseNone)))),      ,
    satisfiedByVariant = if((like("$selectedDomain$", "%SYS%") AND like("$selectedDomain$", "%SW%") AND like("$selectedDomain$", "%HW%") AND like("$selectedDomain$", "%ME%")) OR ((NOT (like("$selectedDomain$", "%SYS%")) AND (NOT like("$selectedDomain$", "%SW%")) AND (NOT like("$selectedDomain$", "%HW%")) AND (NOT like("$selectedDomain$", "%ME%")))), satisfiedByVariant, if(like("$selectedDomain$", "%SYS%"), satisfiedBySysVariant, if(like("$selectedDomain$", "%SW%"), satisfiedBySwVariant, if(like("$selectedDomain$", "%HW%"), satisfiedByHwVariant, satisfiedByMechVariant))))  
| eval 10_Actual = if((((match(",".SatisfiedByLinkRelease.",","$release$") OR SatisfiedByLinkRelease="Not Defined") AND match(",".SatisfactionRelease.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND SatisfiedByLinkReleaseNone=1)) AND match(SatisfiedByReqType,"$selectedDomainRegx$") AND (match(",".satisfiedByVariant.",", "$variant$")),'10_Actual',0) 
| eval 1_Pending = '1_Total' - '1_Actual',
    10_Pending = '10_Total' - '10_Actual' 
| where ('$form.selectedMetrics$'&gt;0) 
| dedup WorkitemID
| eval Contents = if(len(Contents)&gt;`std_getDDContentsCharLimit`, substr(Contents,1,`std_getDDContentsCharLimit`)."....", Contents) 
| rename Status_Workitem as Status, Safety_Workitem as Safety, Security_Workitem as Security, Legal_Workitem as Legal,WorkitemID as "Planning ID", FiledAgainst as "Filed Against",CreationDate as "Creation Date",ClosureDate as "Closure Date"
| table Type,"Planning ID",Summary,"Filed Against",Iteration,Tags,"Issuer Class","Status","Safety","Security","Legal","Creation Date","Closure Date",Implemented_URL</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="count">20</option>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="percentagesRow">false</option>
        <option name="refresh.display">progressbar</option>
        <option name="rowNumbers">false</option>
        <option name="totalsRow">false</option>
        <option name="wrap">true</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Planning ID&quot;">
            <link target="_blank">$row.Implemented_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SysRSidRow">
    <panel id="panelSys " depends="$sys_total_domains$">
      <title>$name$ - BBMID $BBMID$ ($ASPICE$) : $infoMsg$ - &gt;  $SYS_total_done$</title>
      <input type="text" token="contentFiltersys" searchWhenChanged="true">
        <label>Contents filter</label>
        <default></default>
      </input>
      <table id="SysRSid">
        <title>List of DNG IDs / List of requirements affected</title>
        <search>
          <done>
            <set token="SYS_total_done">$job.resultCount$</set>
          </done>
          <query>| loadjob $sysBasesid$ 
| dedup LinkStart_URL 
| eval Domain_DRS = if(`prj_getDRS`, `prj_getDomainDRS_Attribute`, "Not Expected")
| search ($safety$) AND ($legal$) AND ($security$) AND  (Status IN ($ReqStatus$)) AND (ModuleID IN $reqModule$) AND (REQID IN ($reqID$))
| where ($plannedfor$) AND ($verificationLevel$)  AND (like(metricDomains,"$domain$")) AND ($Team_token$) AND ($Domain_DRS$)
| search ($PCR_token$) AND TCStatus IN ($tcStatus$) 
| eval Contents = if(len(Contents)&gt;`std_getDDContentsCharLimit`, substr(Contents,1,`std_getDDContentsCharLimit`)."....", Contents)
| where like(lower(Contents),lower("%$contentFiltersys$%"))
| makemv linked_Implemented
| nomv linked_Implemented
| eval "CR / P linked"=replace(linked_Implemented,";", "; ") 
| makemv Test_Case_Linked
| nomv Test_Case_Linked
| eval Test_Case_Linked=replace(Test_Case_Linked,";", "; ")
| eval ReqVerdict = Verdict 
| where ($VerdictReq$) 
| eval SatisfiesREQID=replace(SatisfiesREQID,",", "; ")
| eval Source_Req_Linked = if ('12_Actual'==1,SatisfiesREQID,if('12_Actual_old'==1,"Not Linked with same Release","Not Linked"))
| rename ModuleID as "Module ID",REQID as "Req. ID",Verification_Level as "Verification Level",Test_Case_Linked as "Test Case Linked", Architectural_Element_Linked as "Architectural Element Linked",Source_Req_Linked as "Source Req. linked",ReqType as "Artifact Type" 
| table "Module ID","Req. ID", Contents, "Artifact Type",Status,Domain_DRS,Safety, Security, Legal,Team,Release,Variant,"Source Req. linked","Architectural Element Linked", "Verification Level", "Test Case Linked", Verdict,"CR / P linked",LinkStart_URL</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="CR / P linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Architectural Element Linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Source Req. linked">
          <colorPalette type="map">{"Not Linked":#FF9797,"Not Linked with same Release":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Req. ID&quot;">
            <link target="_blank">$row.LinkStart_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SysRsTCid" depends="$sys_total_domains$">
    <panel depends="$sys_total_domains$">
      <title>Test-Case Status</title>
      <input type="multiselect" token="Verdict" searchWhenChanged="true">
        <label>Verdict</label>
        <choice value="%">All</choice>
        <choice value="PASSED">PASSED</choice>
        <choice value="FAILED">FAILED</choice>
        <choice value="NOT EXECUTED">NOT EXECUTED</choice>
        <fieldForLabel>Verdict</fieldForLabel>
        <fieldForValue>Verdict</fieldForValue>
        <valuePrefix>like(Verdict,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <default>%</default>
        <initialValue>%</initialValue>
      </input>
      <table>
        <title>List of RQM IDs linked with above requirements / List of test cases ( results ) affected</title>
        <search depends="$sys_total_domains$">
          <query>| loadjob $sysBasesid$ 
| search TestCaseID !=null AND TestCaseID !="Not Defined" 
| search ($safety$) AND ($legal$) AND ($security$) AND (Status IN ($ReqStatus$)) AND (ModuleID IN $reqModule$) AND (REQID IN ($reqID$))
| eval ReqVerdict = Verdict 
| where ($VerdictReq$) 
| where ($plannedfor$) AND ($verificationLevel$) AND (like(metricDomains,"$domain$")) AND ($Team_token$)
| eval Verdict = if((upper(tc_Verdict) == "NOTRUN" OR upper(tc_Verdict) == "BLOCKED" OR upper(tc_Verdict) == "INCOMPLETE" OR upper(tc_Verdict) == "INCONCLUSIVE" OR upper(tc_Verdict) == "PARTIALLYBLOCKED" OR upper(tc_Verdict) == "DEFERRED" OR upper(tc_Verdict) == "INPROGRESS"), "NOT EXECUTED" ,upper(tc_Verdict)) 
| eval Verdict = if(Verdict == "NOT DEFINED", "NOT EXECUTED" ,Verdict) 
| where ($Verdict$)
| search ($PCR_token$) 
| dedup TestCaseID
| rename TestCaseID as "Test Case ID", TestCaseName as Name ,IterationID as "Tested Version",TCERWebID as TCER, TCStatus as Status, TC_Variant as Variant 
| table "Test Case ID", Name, Status, Release, Variant, "Tested Version", TCER, Verdict, LinkEnd_URL</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Test Case ID&quot;">
            <link target="_blank">$row.LinkEnd_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="rowSysImpl" depends="$sys_arch_total_domain$">
    <panel id="panelImplementedSys">
      <title>Linked Change Request / Problem</title>
      <input type="multiselect" token="filedagainst" searchWhenChanged="true">
        <label>Filed Against</label>
        <choice value="%">All</choice>
        <default>%</default>
        <valuePrefix>like(FiledAgainst,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <fieldForLabel>FiledAgainst</fieldForLabel>
        <fieldForValue>FiledAgainst</fieldForValue>
        <search>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_System_Requirements" 
| where _time=max(_time) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,")
| eval FiledAgainst = mvindex(Implement_details,3)
| fillnull value="Not Defined" FiledAgainst
| append [| makeresults | eval FiledAgainst="Not Defined"]
| dedup FiledAgainst
| table  FiledAgainst</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
      </input>
      <input type="multiselect" token="workitemstatus" searchWhenChanged="true">
        <label>Work Item Status</label>
        <choice value="*">Exclude obsolete</choice>
        <default>*</default>
        <valuePrefix>"</valuePrefix>
        <valueSuffix>"</valueSuffix>
        <delimiter> , </delimiter>
        <fieldForLabel>Status</fieldForLabel>
        <fieldForValue>Status</fieldForValue>
        <search>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_System_Requirements" 
| where _time=max(_time) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,")
| eval Status = mvindex(Implement_details,7)
| fillnull value="Not Defined" Status
| append [| makeresults | eval Status="Not Defined"]
| dedup Status
| table  Status</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
      </input>
      <table id="sysReqImpl">
        <search>
          <progress>
            <eval token="workitemidsys">replace($PCR_token$,"ProblemOrChangeReq","WorkitemID")</eval>
          </progress>
          <query>| loadjob $sysBasesid$ 
| fillnull value="Not Defined" FiledAgainst,Status
| search WorkitemID!=null AND WorkitemID!="Not Defined" 
| eval ReqVerdict = Verdict 
| where ($VerdictReq$) 
| search ($safety$) AND ($legal$) AND ($security$) AND (Status IN ($ReqStatus$)) AND (Status_Workitem IN ($workitemstatus$)) AND $workitemidsys$ AND (ModuleID IN $reqModule$) AND (REQID IN ($reqID$))
| where ($plannedfor$) AND ($verificationLevel$) AND (like(metricDomains,"$domain$")) AND ($Team_token$) AND ($filedagainst$)
| eval Verdict = if((upper(tc_Verdict) == "NOTRUN" OR upper(tc_Verdict) == "BLOCKED" OR upper(tc_Verdict) == "INCOMPLETE" OR upper(tc_Verdict) == "INCONCLUSIVE" OR upper(tc_Verdict) == "PARTIALLYBLOCKED" OR upper(tc_Verdict) == "DEFERRED" OR upper(tc_Verdict) == "INPROGRESS"), "NOT EXECUTED" ,upper(tc_Verdict)) 
| eval Verdict = if(Verdict == "NOT DEFINED", "NOT EXECUTED" ,Verdict) 
| where ($Verdict$)
| search ($PCR_token$) 
| dedup WorkitemID
| rename Status_Workitem as Status, Safety_Workitem as Safety, Security_Workitem as Security, Legal_Workitem as Legal,WorkitemID as "Planning ID", FiledAgainst as "Filed Against",CreationDate as "Creation Date",ClosureDate as "Closure Date"
| table Type,"Planning ID",Summary,"Filed Against",Iteration,Tags,"Issuer Class","Status","Safety","Security","Legal","Creation Date","Closure Date",Implemented_URL</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="count">20</option>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="percentagesRow">false</option>
        <option name="refresh.display">progressbar</option>
        <option name="rowNumbers">false</option>
        <option name="totalsRow">false</option>
        <option name="wrap">true</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Planning ID&quot;">
            <link target="_blank">$row.Implemented_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SwArchRSid" depends="$sys_arch_total_domain$">
    <panel id="panelSwArch" depends="$sys_arch_total_domain$">&gt;<title>$name$ - BBMID $BBMID$ ($ASPICE$) : $infoMsg$ - &gt;  $SWArc_done$</title>
      <input type="text" token="contentFilterarch" searchWhenChanged="true">
        <label>Contents filter</label>
        <default></default>
      </input>
      <table>
        <title>List of DNG IDs / List of requirements affected</title>
        <search depends="$sys_arch_total_domain$">--&gt;<done>
            <set token="SWArc_done">$job.resultCount$</set>
          </done>
          <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw"
| where _time=max(_time) 
| fields*
| rename "Sub Model ID" as "Submodelid"
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, RQM_TestArtifacts, Variant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
| search (Submodelid IN ($submodelid$)
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) 
| table Model_ID, Model_Name,Element_Name
    , Element_Type, `std_getReleaseAttribute`, ReleaseNone,
    TC_Count, Requirement_To_Be_Tested_Linked, Variant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, 
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase ,Verdict
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = RQM_TestArtifactsOrderedByExecution 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",",".*") OR ValidatedByLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
            TCValidity = if((((match(",".TCRelease.",",".*") OR TCRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".Variant.",", ",.*,") , 1, 0) 
        | eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
            TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
            TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
            RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
        | eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
        | eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",",".*") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",",".*") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","(,.*,)")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","\(L\)") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
            Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4)),
            ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13))
| search Model_Name="rbx_ccrack_mpci_sw"
| eval 18_Total=if(Model_Name="rbx_ccrack_mpci_sw", 1, 0) 
| eval 18_Actual=if(Model_Name="rbx_ccrack_mpci_sw" AND Requirement_To_Be_Tested_Linked&gt;0,1,0) 
|eval 18_Pending='18_Total'-'18_Actual'
| eval 5_Actual=if(Model_Name="rbx_ccrack_mpci_sw" AND (Requirement_To_Be_Tested_Linked&gt;0 AND Verdict="passed"),1,0)
| eval 5_Total=if(Model_Name="rbx_ccrack_mpci_sw", 1, 0) 
|eval 5_Pending='5_Total'-'5_Actual'
| where ('$form.selectedMetrics$'&gt;0) 
| table Model_ID, Model_Name,Element_Name,Element_Type,LinkEnd_URL,TestCaseID, Verdict, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <format type="color" field="Architectural Element Linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Source Req. linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Req. ID&quot;">
            <link target="_blank">$row.LinkStart_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SwArchRsTCid" depends="$sys_arch_total_domain$">
    <panel id="sys" depends="$sys_arch_total_domain$">
      <title>Test-Case Status</title>
      <input type="multiselect" token="Verdict" searchWhenChanged="true">
        <label>Verdict</label>
        <choice value="%">All</choice>
        <choice value="PASSED">PASSED</choice>
        <choice value="FAILED">FAILED</choice>
        <choice value="NOT EXECUTED">NOT EXECUTED</choice>
        <fieldForLabel>Verdict</fieldForLabel>
        <fieldForValue>Verdict</fieldForValue>
        <valuePrefix>like(Verdict,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <default>%</default>
        <initialValue>%</initialValue>
      </input>
      <table>
        <title>List of RQM IDs linked with above requirements / List of test cases ( results ) affected</title>
        <search>
          <!--depends="$sys_arch_total_domain$">-->
          <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw" 
| where _time=max(_time) 
| fields*
| rename "Sub Model ID" as "Submodelid"
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, RQM_TestArtifacts, Variant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
| search (Submodelid IN ($submodelid$)
| where ((match(",".`std_getReleaseAttribute`.",",".*") AND ".*"!=".*") OR (".*"=".*" AND ReleaseNone=1)) AND (match(",".Variant.",", ",.*,")) AND ($Team_token$)
| table Model_ID, Model_Name,Element_Name
    , Element_Type, `std_getReleaseAttribute`, ReleaseNone,
    TC_Count, Requirement_To_Be_Tested_Linked, Variant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, 
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase ,Verdict 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = RQM_TestArtifactsOrderedByExecution 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",",".*") OR ValidatedByLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",",".*") OR TCRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".Variant.",", ",.*,") , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",",".*") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",",".*") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","(,.*,)")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","\(L\)") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)) ,
    TCERWebID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),1)),
    IterationID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "No Filter Match", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),2)) 
| eval testedInItr=if(((match(",".IterationID.",", ",.*,")) AND TCERWebID!="Not Defined"),1,0) 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0) 
| eventstats count(eval(ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress") AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted",
    values(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by ModuleID,LinkStart_URL, REQID 
| nomv Test_Case_Linked_temp 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| search Model_Name="rbx_ccrack_mpci_sw"
 
| eval Verdict = if((upper(tc_Verdict) == "NOTRUN" OR upper(tc_Verdict) == "BLOCKED" OR upper(tc_Verdict) == "INCOMPLETE" OR upper(tc_Verdict) == "INCONCLUSIVE" OR upper(tc_Verdict) == "PARTIALLYBLOCKED" OR upper(tc_Verdict) == "DEFERRED" OR upper(tc_Verdict) == "INPROGRESS"), "NOT EXECUTED" ,upper(tc_Verdict)) 
| eval Verdict = if(Verdict == "NOT DEFINED", "NOT EXECUTED" ,Verdict) 
| where (like(Verdict,"%")) 
| dedup TestCaseID 
| where ($Verdict$)
|search "TestCaseID"!="Not Defined"
| rename TestCaseID as "Test Case ID", TestCaseName as Name ,IterationID as "Tested Version",TCERWebID as TCER, TCStatus as Status 
| table "Test Case ID", Name, Status, Release, Variant, "Tested Version", TCER, Verdict</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Test Case ID&quot;">
            <link target="_blank">$row.LinkEnd_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SysArchRSid" depends="$sys_total_domain$">
    <panel id="panelSysArch" depends="$sys_total_domain$">
      <title>$name$ - BBMID $BBMID$ ($ASPICE$) : $infoMsg$ - &gt;  $SYSARC_Total_done$</title>
      <input type="text" token="contentFilterarch" searchWhenChanged="true">
        <label>Contents filter</label>
        <default></default>
      </input>
      <table>
        <title>List of DNG IDs / List of requirements affected</title>
        <search depends="$sys_total_domain$">
          <done>
            <set token="SYSARC_Total_done">$job.resultCount$</set>
          </done>
          <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw"
| where _time=max(_time) 
| fields*
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, RQM_TestArtifacts, Variant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
```| search (Submodelid IN ($submodelid$))```
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) 
| table Model_ID, Model_Name,Element_Name,ElementPath,
    , Element_Type, `std_getReleaseAttribute`, ReleaseNone,
    TC_Count, Requirement_To_Be_Tested_Linked, Variant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, Element_URL,
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase ,Verdict 
| dedup Element_URL 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = RQM_TestArtifactsOrderedByExecution 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".TC_Variant.",", "$variant$") , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND "$release$"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","$testedVersion$")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","\(L\)") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)) 
| eventstats count(eval(ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress") AND ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted" by Element_URL 
| search Model_Name="CentralComputingRack_SysArch"
| eval 2_Total=if(Model_Name="CentralComputingRack_SysArch", 1, 0) 
| eval 2_Actual=if(Model_Name="CentralComputingRack_SysArch" AND (Requirement_To_Be_Tested_Linked&gt;0 AND Verdict="passed"),1,0) 
| eval 2_Pending='2_Total'-'2_Actual' 
| eval 14_Actual=if(Model_Name="CentralComputingRack_SysArch" AND Requirement_To_Be_Tested_Linked&gt;0,1,0) 
| eval 14_Total=if(Model_Name="CentralComputingRack_SysArch", 1, 0) 
| eval 14_Pending='14_Total'-'14_Actual' 
| where ('$form.selectedMetrics$'&gt;0) 
| table Model_ID, Model_Name,Element_Name,ElementPath,Element_Type,LinkEnd_URL,TestCaseID, Verdict, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <format type="color" field="Architectural Element Linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Source Req. linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Req. ID&quot;">
            <link target="_blank">$row.LinkStart_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SysArchRsTCid" depends="$sys_total_domain$">
    <panel id="panelSysarch" depends="$sys_total_domain$">
      <!-- depends="$sys_arch_total_domain$">-->
      <title>Test-Case Status</title>
      <input type="multiselect" token="Verdict" searchWhenChanged="true">
        <label>Verdict</label>
        <choice value="%">All</choice>
        <choice value="PASSED">PASSED</choice>
        <choice value="FAILED">FAILED</choice>
        <choice value="NOT EXECUTED">NOT EXECUTED</choice>
        <fieldForLabel>Verdict</fieldForLabel>
        <fieldForValue>Verdict</fieldForValue>
        <valuePrefix>like(Verdict,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <default>%</default>
        <initialValue>%</initialValue>
      </input>
      <table>
        <title>List of RQM IDs linked with above requirements / List of test cases ( results ) affected</title>
        <search depends="$sys_total_domain$">
          <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw"
| where _time=max(_time) 
| fields*
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, RQM_TestArtifacts, Variant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
```| search (Submodelid IN ($submodelid$)) AND (Component IN ($component$))```
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) 
| table Model_ID, Model_Name,Element_Name
    , Element_Type, `std_getReleaseAttribute`, ReleaseNone,
    TC_Count, Requirement_To_Be_Tested_Linked, Variant,TC_Variant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, 
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase ,Verdict 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = RQM_TestArtifactsOrderedByExecution 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".TC_Variant.",", "$variant$") , 1, 0)
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND "$release$"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","$testedVersion$")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","\(L\)") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)) ,
    TCERWebID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),1)),
    IterationID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "No Filter Match", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),2)) 
| eval testedInItr=if(((match(",".IterationID.",", ",.*,")) AND TCERWebID!="Not Defined"),1,0) 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0) 
| eventstats count(eval(ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress") AND ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted",
    values(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by Element_URL
| nomv Test_Case_Linked_temp 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| search Model_Name="CentralComputingRack_SysArch"
| eval Verdict = if((upper(tc_Verdict) == "NOTRUN" OR upper(tc_Verdict) == "BLOCKED" OR upper(tc_Verdict) == "INCOMPLETE" OR upper(tc_Verdict) == "INCONCLUSIVE" OR upper(tc_Verdict) == "PARTIALLYBLOCKED" OR upper(tc_Verdict) == "DEFERRED" OR upper(tc_Verdict) == "INPROGRESS"), "NOT EXECUTED" ,upper(tc_Verdict)) 
| eval Verdict = if(Verdict == "NOT DEFINED", "NOT EXECUTED" ,Verdict) 
| where (like(Verdict,"%")) 
| dedup TestCaseID 
| where ($Verdict$)
|search "TestCaseID"!="Not Defined"
| rename TestCaseID as "Test Case ID", TestCaseName as Name ,IterationID as "Tested Version",TCERWebID as TCER, TCStatus as Status 
| table "Test Case ID", Name, Status, Release, TC_Variant, "Tested Version", TCER, Verdict</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Test Case ID&quot;">
            <link target="_blank">$row.LinkEnd_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SwRSidRow" depends="$sw_total_domain$">
    <panel id="panelSW " depends="$sw_total_domain$">
      <title>$name$ - BBMID $BBMID$ ($ASPICE$) : $infoMsg$ - &gt;  $SWREQ_done$</title>
      <input type="text" token="contentFiltersw" searchWhenChanged="true">
        <label>Contents filter</label>
        <default></default>
      </input>
      <table id="SwRSid">
        <title>List of DNG IDs / List of requirements affected</title>
        <search depends="$sw_total_domain$">
          <done>
            <set token="SWREQ_done">$job.resultCount$</set>
          </done>
          <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw"
|fields*
| search Element_Type IN ($element_type$)
| where _time=max(_time) 
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, RQM_TestArtifacts, Variant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
| search (Submodelid IN ($submodelid$)) AND (Component IN ($component$)) 
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) 
| table Model_ID, Model_Name,Element_Name,Component,Submodelid,ElementPath,
    , Element_Type, `std_getReleaseAttribute`, ReleaseNone,
    TC_Count, Requirement_To_Be_Tested_Linked, Variant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, Element_URL,
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase ,Verdict 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = RQM_TestArtifactsOrderedByExecution 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",",".*") OR ValidatedByLinkRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",",".*") OR TCRelease="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".Variant.",", ",.*,") , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",",".*") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",",".*") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND ".*"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","(,.*,)")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","\(L\)") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)) 
| eventstats count(eval(ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress") AND ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted" by Element_URL 
| dedup Element_URL 
| search Model_Name="rbx_ccrack_mpci_sw" 
| eval 18_Total=if(Model_Name="rbx_ccrack_mpci_sw", 1, 0) 
| eval 18_Actual=if(Model_Name="rbx_ccrack_mpci_sw" AND Requirement_To_Be_Tested_Linked&gt;0,1,0) 
| eval 18_Pending='18_Total'-'18_Actual' 
| eval 5_Actual=if(Model_Name="rbx_ccrack_mpci_sw" AND (Requirement_To_Be_Tested_Linked&gt;0 AND Verdict="passed"),1,0) 
| eval 5_Total=if(Model_Name="rbx_ccrack_mpci_sw", 1, 0) 
| eval 5_Pending='5_Total'-'5_Actual' 
| where ('$form.selectedMetrics$'&gt;0) 
|rename Submodelid as "Sub Model ID"
| table Model_ID, "Sub Model ID",Component,Model_Name,Element_Name,ElementPath,Element_Type,LinkEnd_URL,TestCaseID, Verdict, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="CR / P linked">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <format type="color" field="SW ARCH element linked (trace)">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="SW ARCH element linked (satisfy)">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="SW ARCH element linked (refine)">
          <colorPalette type="map">{"Not Linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Source Req. linked">
          <colorPalette type="map">{"Not Linked":#FF9797,"Not Linked with same Release":#FF9797}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Req. ID&quot;">
            <link target="_blank">$row.LinkStart_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="SwRsTCid" depends="$sw_total_domain$">
    <panel depends="$sw_total_domain$">
      <title>Test-Case Status</title>
      <input type="multiselect" token="Verdict" searchWhenChanged="true">
        <label>Verdict</label>
        <choice value="%">All</choice>
        <choice value="PASSED">PASSED</choice>
        <choice value="FAILED">FAILED</choice>
        <choice value="NOT EXECUTED">NOT EXECUTED</choice>
        <fieldForLabel>Verdict</fieldForLabel>
        <fieldForValue>Verdict</fieldForValue>
        <valuePrefix>like(Verdict,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <default>%</default>
        <initialValue>%</initialValue>
      </input>
      <table>
        <title>List of RQM IDs linked with above requirements / List of test cases ( results ) affected</title>
        <search depends="$sw_total_domain$">
          <query>(index=`std_getBaseIndex` OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_architecture_sys_sw"
| where _time=max(_time) 
| fields* 
| search Element_Type IN ($element_type$)
| fillnull value="" Contents 
| fillnull value="Not Defined" `std_getReleaseAttribute`, RQM_TestArtifacts, Variant,`std_getStkhModule` 
| fillnull value="Not Linked" "Architectural_Element_Linked" 
| eval SatisfiesREQID = replace('SatisfiesREQID',"Not Defined", "Not Linked") 
| eval Security = lower(Security), Legal = lower(Legal) 
| eval Architectural_Element_Linked = replace('Architectural_Element_Linked',"Not Defined", "Not Linked") 
| fillnull value=1 ReleaseNone, SatisfiesLinkReleaseNone, DesignLinkReleaseNone 
| rename `std_getStkhModule` as stkhModule 
| eval stRSProcessed = split(stkhModule,"; ") 
| search (Submodelid IN ($submodelid$)) AND (Component IN ($component$)) 
| where ((match(",".`std_getReleaseAttribute`.",","$release$") AND "$release$"!=".*") OR ("$release$"=".*" AND ReleaseNone=1)) AND (match(",".TC_Variant.",", "$variant$")) 
| table Model_ID, Model_Name,Element_Name,Submodelid,Component
    , Element_Type, `std_getReleaseAttribute`, ReleaseNone,
    TC_Count, Requirement_To_Be_Tested_Linked, Variant,
    ValidatedByLinkName, ValidatedByLinkRelease, ValidatedByLinkReleaseNone, Element_URL,TC_Variant,
    TCRelease, TCReleaseNone, LinkEnd_URL, TestCaseID, TestCaseUUID, TestCaseName, TestCaseState,Test_Level,TCStatus,TestSuiteID, TestPlanID, Variant,
    RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution, TC_Count, NoTestcase ,Verdict 
| eval RQM_TestArtifactsOrderedByExecution = if(isnull(RQM_TestArtifactsOrderedByExecution) or RQM_TestArtifactsOrderedByExecution="", RQM_TestArtifacts, RQM_TestArtifactsOrderedByExecution) 
| eval RQM_TestArtifacts = RQM_TestArtifactsOrderedByExecution 
| eval LinkValidity = if((((match(",".ValidatedByLinkRelease.",","$release$") OR ValidatedByLinkRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND ValidatedByLinkReleaseNone=1)) , 1 , 0),
    TCValidity = if((((match(",".TCRelease.",","$release$") OR TCRelease="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND TCReleaseNone=1)) AND LinkValidity=1 AND match(",".TC_Variant.",", "$variant$") , 1, 0) 
| eval ValidatedByLinkName=if(TCValidity=1, ValidatedByLinkName, "Not Defined"),
    TestCaseID=if(TCValidity=1, TestCaseID, "Not Defined"),
    TestPlanID=if(TCValidity=1, TestPlanID, "Not Defined"),
    RQM_TestArtifacts=if(TCValidity=1, RQM_TestArtifacts, "Not Defined") 
| eval RQM_TestArtifacts = split(RQM_TestArtifacts,"||") 
| eval RQM_TestArtifactsFiltered = mvfilter((((match(",".mvindex(split(RQM_TestArtifacts,".,"),5).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),5)=="Not Defined") AND "$release$"!=".*") OR (".*"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),6)=="1")) AND (((match(",".mvindex(split(RQM_TestArtifacts,".,"),8).",","$release$") OR mvindex(split(RQM_TestArtifacts,".,"),8)=="Not Defined") AND "$release$"!=".*") OR ("$release$"=".*" AND mvindex(split(RQM_TestArtifacts,".,"),9)=="1") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),9))) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),2).",","$testedVersion$")) AND (match(",".mvindex(split(RQM_TestArtifacts,".,"),11).",","\(L\)") OR isnull(mvindex(split(RQM_TestArtifacts,".,"),11)))),
    Verdict=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),4)),
    ProblemID = if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "Not Defined", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),13)) ,
    TCERWebID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "-", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),1)),
    IterationID=if(isnull(RQM_TestArtifactsFiltered) or RQM_TestArtifactsFiltered="", "No Filter Match", mvindex(split(mvindex(RQM_TestArtifactsFiltered,0),".,"),2)) 
| eval testedInItr=if(((match(",".IterationID.",", ",.*,")) AND TCERWebID!="Not Defined"),1,0) 
| eval Verdict=if(testedInItr==1,Verdict,"Not Defined"), 
    tc_Verdict =split(Verdict, "."),
    TCERWebID=if(testedInItr==1,TCERWebID,"-"),
    IterationID=if(testedInItr==1,IterationID,"No Filter Match") 
| eval tc_Verdict=mvindex(tc_Verdict, mvcount(tc_Verdict)-1), 
    Requirement_To_Be_Tested_Linked = if((TCValidity=1) ,Requirement_To_Be_Tested_Linked,0) 
| eventstats count(eval(ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as TC_Count,
    count(eval((Verdict="com.ibm.rqm.execution.common.state.passed" OR Verdict="passed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Passed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.failed" OR Verdict="com.ibm.rqm.execution.common.state.permfailed" OR Verdict="failed" OR Verdict="permfailed") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Failed, 
    count(eval((Verdict="com.ibm.rqm.execution.common.state.error" OR Verdict="error") AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as Error, 
    count(eval(Verdict IN ("com.ibm.rqm.execution.common.state.blocked", "com.ibm.rqm.execution.common.state.paused", "com.ibm.rqm.execution.common.state.incomplete", "com.ibm.rqm.execution.common.state.inconclusive", "com.ibm.rqm.execution.common.state.partiallyblocked", "com.ibm.rqm.execution.common.state.deferred", "Not Defined","com.ibm.rqm.execution.common.state.inprogress", "blocked", "paused", "incomplete", "inconclusive", "partiallyblocked", "deferred", "Not Defined","inprogress") AND ValidatedByLinkName="validatesArchitectureElement" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "NotExecuted",
    values(Valid_TestCaseID) delim=";" as Test_Case_Linked_temp,
    count(eval(Status!="obsolete" AND ValidatedByLinkName="Validated By" AND TestCaseID !="Not Defined" AND TestPlanID !="Not Defined")) as "Linked by test case", 
    count(eval(Status!="obsolete" AND (NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0)) )) as "Not linked by test case", 
    count(eval(Status!="obsolete")) as "To be tested",
    max(Requirement_To_Be_Tested_Linked) as Requirement_To_Be_Tested_Linked by Element_URL 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") , General=1 
| dedup Element_URL 
| nomv Test_Case_Linked_temp 
| eval Test_Case_Linked = Test_Case_Linked_temp 
| eval Test_Case_Linked = if((NoTestcase=1 OR (Passed =0 AND Failed = 0 AND Error = 0 AND NotExecuted = 0) OR TestCaseID == "Not Defined") ,"Not linked",Test_Case_Linked) 
| eval Verdict = case(Failed &gt; 0,"FAILED",((Error&gt;0)),"ERROR",((NotExecuted&gt;0) AND (TC_Count&gt;0)),"NOT EXECUTED",(TC_Count==Passed AND NoTestcase==0 AND TC_Count&gt;0),"PASSED",1=1, "NA") 
| search Model_Name="rbx_ccrack_mpci_sw"
| eval Verdict = if((upper(tc_Verdict) == "NOTRUN" OR upper(tc_Verdict) == "BLOCKED" OR upper(tc_Verdict) == "INCOMPLETE" OR upper(tc_Verdict) == "INCONCLUSIVE" OR upper(tc_Verdict) == "PARTIALLYBLOCKED" OR upper(tc_Verdict) == "DEFERRED" OR upper(tc_Verdict) == "INPROGRESS"), "NOT EXECUTED" ,upper(tc_Verdict)) 
| eval Verdict = if(Verdict == "NOT DEFINED", "NOT EXECUTED" ,Verdict) 
| where (like(Verdict,"%")) 
| dedup TestCaseID 
| where ($Verdict$) 
| search "TestCaseID"!="Not Defined" 
| rename TestCaseID as "Test Case ID", TestCaseName as Name ,IterationID as "Tested Version",TCERWebID as TCER, TCStatus as Status ,Submodelid as "Sub Model ID"
| table "Test Case ID", Name, Status, Release, TC_Variant, "Tested Version", TCER, Verdict</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="refresh.display">progressbar</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Test Case ID&quot;">
            <link target="_blank">$row.LinkEnd_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
  <row id="rowSWImpl" depends="$sw_total_domains$">
    <panel id="panelImplementedSW">
      <title>Linked Change Request / Problem</title>
      <input type="multiselect" token="filedagainst" searchWhenChanged="true">
        <label>Filed Against</label>
        <choice value="%">All</choice>
        <default>%</default>
        <valuePrefix>like(FiledAgainst,"</valuePrefix>
        <valueSuffix>")</valueSuffix>
        <delimiter> OR </delimiter>
        <fieldForLabel>FiledAgainst</fieldForLabel>
        <fieldForValue>FiledAgainst</fieldForValue>
        <search>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_Software_Requirements" 
| where _time=max(_time) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,") 
| eval FiledAgainst = mvindex(Implement_details,3)
| fillnull value="Not Defined" FiledAgainst
| append [| makeresults | eval FiledAgainst="Not Defined"]
| dedup FiledAgainst
| table  FiledAgainst</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
      </input>
      <input type="multiselect" token="workitemstatus" searchWhenChanged="true">
        <label>Work Item Status</label>
        <choice value="*">Exclude obsolete</choice>
        <default>*</default>
        <valuePrefix>"</valuePrefix>
        <valueSuffix>"</valueSuffix>
        <delimiter> , </delimiter>
        <fieldForLabel>Status</fieldForLabel>
        <fieldForValue>Status</fieldForValue>
        <search>
          <query>(index=`std_getBaseIndex`  OR index=`std_getSummaryIndex` OR index=`std_getMUIndex`) source="Summary_STD_Quality_Dashboard_Software_Requirements" 
| where _time=max(_time) 
| eval Implement_details = split(Implement_details,"||") 
| mvexpand Implement_details 
| eval Implement_details = split(Implement_details,".,") 
| eval Status = mvindex(Implement_details,7)
| fillnull value="Not Defined" Status
| append [| makeresults | eval Status="Not Defined"]
| dedup Status
| table  Status</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
      </input>
      <table id="swReqImpl">
        <search>
          <progress>
            <eval token="workitemidsw">replace($PCR_token$,"ProblemOrChangeReq","WorkitemID")</eval>
          </progress>
          <query>| loadjob $swreqsid$ 
| fillnull value="Not Defined" FiledAgainst,Status
| search WorkitemID!=null AND WorkitemID!="Not Defined" 
| eval ReqVerdict = Verdict 
| where ($VerdictReq$) 
| search ($safety$) AND ($legal$) AND ($security$) AND (Status IN ($ReqStatus$)) AND (Status_Workitem IN ($workitemstatus$)) AND $workitemidsw$ AND (ModuleID IN $reqModule$) AND (REQID IN ($reqID$))
| where ($plannedfor$) AND ($verificationLevel$) AND (like(ReqDomain,"$domain$")) AND (like(metricDomains,"$domain$")) AND ($Team_token$) AND ($filedagainst$)
| search ($PCR_token$) 
| eval Verdict = if((upper(tc_Verdict) == "NOTRUN" OR upper(tc_Verdict) == "BLOCKED" OR upper(tc_Verdict) == "INCOMPLETE" OR upper(tc_Verdict) == "INCONCLUSIVE" OR upper(tc_Verdict) == "PARTIALLYBLOCKED" OR upper(tc_Verdict) == "DEFERRED" OR upper(tc_Verdict) == "INPROGRESS"), "NOT EXECUTED" ,upper(tc_Verdict)) 
| eval Verdict = if(Verdict == "NOT DEFINED", "NOT EXECUTED" ,Verdict) 
| where ($Verdict$)
| dedup WorkitemID
| rename Status_Workitem as Status, Safety_Workitem as Safety, Security_Workitem as Security, Legal_Workitem as Legal,WorkitemID as "Planning ID", FiledAgainst as "Filed Against",CreationDate as "Creation Date",ClosureDate as "Closure Date"
| table Type,"Planning ID",Summary,"Filed Against",Iteration,Tags,"Issuer Class","Status","Safety","Security","Legal","Creation Date","Closure Date",Implemented_URL</query>
          <earliest>$date_earliest$</earliest>
          <latest>$date_latest$</latest>
        </search>
        <option name="count">20</option>
        <option name="dataOverlayMode">none</option>
        <option name="drilldown">cell</option>
        <option name="percentagesRow">false</option>
        <option name="refresh.display">progressbar</option>
        <option name="rowNumbers">false</option>
        <option name="totalsRow">false</option>
        <option name="wrap">true</option>
        <format type="color" field="Test Case Linked">
          <colorPalette type="map">{"Not linked":#FF9797}</colorPalette>
        </format>
        <format type="color" field="Verdict">
          <colorPalette type="map">{"PASSED":#C2E59D,"FAILED":#FF9797,"NOT EXECUTED":#FFF1B3}</colorPalette>
        </format>
        <drilldown>
          <condition match="'click.name2'==&quot;Planning ID&quot;">
            <link target="_blank">$row.Implemented_URL|n$</link>
          </condition>
          <condition></condition>
        </drilldown>
      </table>
    </panel>
  </row>
</form>
